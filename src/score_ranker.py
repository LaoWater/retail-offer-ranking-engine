"""
Ranker scoring for Metro Personalized Offers Recommender.

Scores all candidate (customer, offer) pairs with the trained model
and writes top-N recommendations per customer.
"""

import logging

import numpy as np
import pandas as pd

from src.config import TOP_N_RECOMMENDATIONS, FEATURE_COLUMNS
from src.features import build_interaction_features

logger = logging.getLogger(__name__)


def score_candidates(model, run_date, conn):
    """
    Score all candidates in the pool and write top-N to recommendations.

    Args:
        model: trained sklearn/lgbm model with predict_proba
        run_date: str, date of this run
        conn: SQLite connection
    """
    logger.info("Scoring candidates...")

    # Step 1: Load candidate pool
    candidates = pd.read_sql(
        "SELECT customer_id, offer_id FROM candidate_pool WHERE run_date = ?",
        conn,
        params=(run_date,),
    )

    if candidates.empty:
        logger.warning("No candidates to score for %s", run_date)
        return 0

    logger.info(f"  Candidate pairs to score: {len(candidates):,}")

    # Step 2: Load feature tables
    cust_feats = pd.read_sql("SELECT * FROM customer_features", conn)
    cust_feat_cols = [
        "customer_id", "recency_days", "frequency", "monetary",
        "promo_affinity", "avg_basket_size", "category_entropy", "avg_discount_depth",
    ]
    cust_feats = cust_feats[[c for c in cust_feat_cols if c in cust_feats.columns]]

    offer_feats = pd.read_sql("SELECT * FROM offer_features", conn)
    offer_feat_cols = [
        "offer_id", "discount_depth", "margin_impact",
        "days_until_expiry", "historical_redemption_rate",
    ]
    offer_feats = offer_feats[[c for c in offer_feat_cols if c in offer_feats.columns]]

    # Step 3: Compute interaction features
    interaction_feats = build_interaction_features(conn, candidates, run_date)

    # Step 4: Merge all features
    scored = candidates.merge(cust_feats, on="customer_id", how="left")
    scored = scored.merge(offer_feats, on="offer_id", how="left")
    scored = scored.merge(
        interaction_feats, on=["customer_id", "offer_id"], how="left"
    )

    # Fill NaN for cold-start / missing features
    scored = scored.fillna(0)

    # Step 5: Predict P(redemption)
    feature_cols = [c for c in FEATURE_COLUMNS if c in scored.columns]
    X = scored[feature_cols].values.astype(np.float32)
    scores = model.predict_proba(X)[:, 1]
    scored["score"] = scores

    # Step 6: Rank within each customer, take top-N
    scored["rank"] = (
        scored.groupby("customer_id")["score"]
        .rank(ascending=False, method="first")
        .astype(int)
    )
    top_n = scored[scored["rank"] <= TOP_N_RECOMMENDATIONS].copy()

    # Step 7: Write to recommendations table (idempotent)
    conn.execute("DELETE FROM recommendations WHERE run_date = ?", (run_date,))

    top_n["run_date"] = run_date
    recs_df = top_n[["run_date", "customer_id", "offer_id", "score", "rank"]]

    recs_df.to_sql("recommendations", conn, if_exists="append", index=False)
    conn.commit()

    n_customers = recs_df["customer_id"].nunique()
    logger.info(
        f"  Recommendations written: {len(recs_df):,} "
        f"(top-{TOP_N_RECOMMENDATIONS} for {n_customers:,} customers)"
    )
    return len(recs_df)
