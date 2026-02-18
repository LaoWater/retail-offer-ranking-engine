"""
Ranker training for Metro Personalized Offers Recommender.

Trains both Logistic Regression and LightGBM models, selects the best
by validation AUC, and saves the winning model artifact.
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report
from lightgbm import LGBMClassifier

from src.config import (
    SEED, FEATURE_COLUMNS, LGBM_PARAMS, NEGATIVE_SAMPLE_RATIO,
    REDEMPTION_WINDOW_DAYS, MODELS_DIR,
)
from src.features import build_interaction_features

logger = logging.getLogger(__name__)


def build_training_set(conn, reference_date):
    """
    Build labeled training set from impressions and redemptions.

    Positives: impression that led to redemption within 7 days.
    Negatives: impression with no redemption (downsampled).

    Returns: (X, y, feature_names) where X is a numpy array.
    """
    logger.info("Building training set...")

    # Step 1: Label impressions
    labeled = pd.read_sql("""
        SELECT
            i.impression_id,
            i.customer_id,
            i.offer_id,
            i.shown_timestamp,
            CASE WHEN r.redemption_id IS NOT NULL THEN 1 ELSE 0 END AS label
        FROM impressions i
        LEFT JOIN redemptions r
            ON i.customer_id = r.customer_id
            AND i.offer_id = r.offer_id
            AND JULIANDAY(r.redeemed_timestamp) BETWEEN JULIANDAY(i.shown_timestamp)
                AND JULIANDAY(i.shown_timestamp) + :window
        WHERE JULIANDAY(i.shown_timestamp) <= JULIANDAY(:ref)
    """, conn, params={"ref": reference_date, "window": REDEMPTION_WINDOW_DAYS})

    # Deduplicate: if multiple impressions led to same redemption, keep one
    labeled = labeled.drop_duplicates(subset=["customer_id", "offer_id", "label"])

    positives = labeled[labeled["label"] == 1]
    negatives = labeled[labeled["label"] == 0]

    logger.info(
        f"  Raw labels: {len(positives):,} positives, {len(negatives):,} negatives"
    )

    # Step 2: Downsample negatives
    n_neg = min(len(negatives), len(positives) * NEGATIVE_SAMPLE_RATIO)
    if n_neg > 0:
        negatives_sampled = negatives.sample(n=n_neg, random_state=SEED)
    else:
        negatives_sampled = negatives

    training_set = pd.concat([positives, negatives_sampled], ignore_index=True)
    training_set = training_set.sample(frac=1.0, random_state=SEED).reset_index(drop=True)

    logger.info(
        f"  Training set: {len(training_set):,} rows "
        f"({training_set['label'].mean() * 100:.1f}% positive)"
    )

    # Step 3: Join features
    pairs = training_set[["customer_id", "offer_id"]].copy()

    # Customer features
    cust_feats = pd.read_sql("SELECT * FROM customer_features", conn)
    cust_feat_cols = [
        "customer_id", "recency_days", "frequency", "monetary",
        "promo_affinity", "avg_basket_size", "category_entropy", "avg_discount_depth",
        "avg_basket_quantity", "tier2_purchase_ratio", "tier3_purchase_ratio",
        "fresh_category_ratio", "business_order_ratio",
    ]
    cust_feats = cust_feats[[c for c in cust_feat_cols if c in cust_feats.columns]]

    # Offer features
    offer_feats = pd.read_sql("SELECT * FROM offer_features", conn)
    offer_feat_cols = [
        "offer_id", "discount_depth", "margin_impact",
        "days_until_expiry", "historical_redemption_rate", "is_own_brand",
    ]
    offer_feats = offer_feats[[c for c in offer_feat_cols if c in offer_feats.columns]]

    # Interaction features
    interaction_feats = build_interaction_features(conn, pairs, reference_date)

    # Merge everything
    merged = training_set.merge(cust_feats, on="customer_id", how="left")
    merged = merged.merge(offer_feats, on="offer_id", how="left")
    merged = merged.merge(
        interaction_feats, on=["customer_id", "offer_id"], how="left"
    )

    # Fill NaN
    merged = merged.fillna(0)

    # Guard against feature-config drift by materializing any missing model features.
    missing_feature_cols = [c for c in FEATURE_COLUMNS if c not in merged.columns]
    if missing_feature_cols:
        logger.warning(
            "Missing feature columns in training set; defaulting to 0.0: %s",
            missing_feature_cols,
        )
        for col in missing_feature_cols:
            merged[col] = 0.0

    # Extract features and labels
    X = merged[FEATURE_COLUMNS].values.astype(np.float32)
    y = merged["label"].values.astype(np.int32)

    logger.info(f"  Feature matrix shape: {X.shape}")
    return X, y, FEATURE_COLUMNS


def train_ranker(conn, reference_date=None):
    """
    Train the ranking model and save the best artifact.

    Trains both LR and LightGBM, picks the one with higher validation AUC.

    Returns: (model, metrics_dict)
    """
    if reference_date is None:
        reference_date = datetime.now().strftime("%Y-%m-%d")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Build training data
    X, y, feature_names = build_training_set(conn, reference_date)

    if len(X) == 0:
        logger.error("No training data available!")
        return None, {}

    # Temporal-ish split: use last 20% of the shuffled set as validation
    # (data was already shuffled during build_training_set)
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    logger.info(
        f"  Train: {len(X_train):,} rows, Val: {len(X_val):,} rows"
    )

    metrics = {}

    # ---- Train Logistic Regression ----
    logger.info("Training Logistic Regression...")
    t0 = time.time()
    lr_model = LogisticRegression(
        max_iter=500, class_weight="balanced", random_state=SEED, solver="lbfgs"
    )
    lr_model.fit(X_train, y_train)
    lr_time = time.time() - t0

    lr_val_proba = lr_model.predict_proba(X_val)[:, 1]
    lr_auc = roc_auc_score(y_val, lr_val_proba) if len(np.unique(y_val)) > 1 else 0.5
    metrics["lr_auc"] = round(lr_auc, 4)
    metrics["lr_train_time_s"] = round(lr_time, 2)
    logger.info(f"  LR - AUC: {lr_auc:.4f} (trained in {lr_time:.1f}s)")

    # Feature importance (coefficients)
    lr_importance = dict(zip(feature_names, lr_model.coef_[0].tolist()))

    # ---- Train LightGBM ----
    logger.info("Training LightGBM...")
    t0 = time.time()
    lgbm_model = LGBMClassifier(**LGBM_PARAMS)
    lgbm_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="auc",
    )
    lgbm_time = time.time() - t0

    lgbm_val_proba = lgbm_model.predict_proba(X_val)[:, 1]
    lgbm_auc = roc_auc_score(y_val, lgbm_val_proba) if len(np.unique(y_val)) > 1 else 0.5
    metrics["lgbm_auc"] = round(lgbm_auc, 4)
    metrics["lgbm_train_time_s"] = round(lgbm_time, 2)
    logger.info(f"  LightGBM - AUC: {lgbm_auc:.4f} (trained in {lgbm_time:.1f}s)")

    # Feature importance (gain-based)
    lgbm_importance = dict(zip(feature_names, lgbm_model.feature_importances_.tolist()))

    # ---- Pick the winner ----
    if lgbm_auc >= lr_auc:
        best_model = lgbm_model
        best_name = "lightgbm"
        best_auc = lgbm_auc
        best_importance = lgbm_importance
    else:
        best_model = lr_model
        best_name = "logistic_regression"
        best_auc = lr_auc
        best_importance = lr_importance

    metrics["best_model"] = best_name
    metrics["best_auc"] = round(best_auc, 4)
    metrics["feature_importance"] = best_importance

    logger.info(f"  Winner: {best_name} (AUC={best_auc:.4f})")

    # ---- Save artifact ----
    artifact = {
        "model": best_model,
        "model_name": best_name,
        "feature_names": feature_names,
        "train_date": reference_date,
        "metrics": metrics,
        "lr_model": lr_model,
        "lgbm_model": lgbm_model,
    }
    artifact_path = MODELS_DIR / "ranker_latest.pkl"
    joblib.dump(artifact, artifact_path)
    logger.info(f"  Artifact saved to {artifact_path}")

    return best_model, metrics


def load_model():
    """Load the latest model artifact."""
    artifact_path = MODELS_DIR / "ranker_latest.pkl"
    if not artifact_path.exists():
        raise FileNotFoundError(f"No model found at {artifact_path}. Run training first.")
    artifact = joblib.load(artifact_path)
    logger.info(
        f"Loaded model: {artifact['model_name']} "
        f"(trained {artifact['train_date']}, AUC={artifact['metrics']['best_auc']:.4f})"
    )
    return artifact["model"], artifact
