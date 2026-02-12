"""
Drift monitoring for Metro Personalized Offers Recommender.

Uses Population Stability Index (PSI) to detect feature distribution shifts
between the training period and current data. Triggers retraining when
multiple features exceed thresholds.
"""

import logging
from typing import List, Dict

import numpy as np
import pandas as pd

from src.config import (
    PSI_WARN_THRESHOLD, PSI_ALERT_THRESHOLD,
    DRIFT_RETRAIN_MIN_FEATURES, DRIFT_FEATURES, MODELS_DIR,
)

logger = logging.getLogger(__name__)


def compute_psi(baseline: np.ndarray, current: np.ndarray, n_bins=10) -> float:
    """
    Compute Population Stability Index between two distributions.

    PSI = sum( (current_pct - baseline_pct) * ln(current_pct / baseline_pct) )

    Interpretation:
      < 0.10 : No significant shift
      0.10 - 0.25 : Moderate shift (investigate)
      >= 0.25 : Large shift (retrain)

    Args:
        baseline: array of feature values from training period
        current: array of feature values from current period
        n_bins: number of histogram bins

    Returns:
        PSI value (float >= 0)
    """
    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    # Use baseline to define bin edges
    _, bin_edges = np.histogram(baseline, bins=n_bins)

    baseline_counts, _ = np.histogram(baseline, bins=bin_edges)
    current_counts, _ = np.histogram(current, bins=bin_edges)

    # Convert to proportions with epsilon smoothing to avoid log(0)
    eps = 1e-4
    baseline_pct = (baseline_counts + eps) / (baseline_counts.sum() + eps * n_bins)
    current_pct = (current_counts + eps) / (current_counts.sum() + eps * n_bins)

    # PSI formula
    psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
    return float(max(0.0, psi))


def check_drift(conn, run_date) -> List[Dict]:
    """
    Check feature drift for all monitored features.

    Compares current feature distributions against the training period baseline.
    Logs results to drift_log table.

    Returns:
        List of alert dicts: [{'feature': str, 'psi': float, 'severity': str}]
    """
    logger.info("Checking feature drift...")

    # Get baseline date from model artifact
    baseline_date = _get_baseline_date()

    # Load baseline features (from training period)
    baseline_feats = _load_feature_snapshot(conn, baseline_date)
    current_feats = _load_feature_snapshot(conn, run_date)

    if baseline_feats is None or current_feats is None:
        logger.warning("Cannot compute drift: missing feature snapshots")
        return []

    alerts = []
    all_results = []

    for feature in DRIFT_FEATURES:
        if feature not in baseline_feats.columns or feature not in current_feats.columns:
            continue

        baseline_vals = baseline_feats[feature].dropna().values
        current_vals = current_feats[feature].dropna().values

        psi = compute_psi(baseline_vals, current_vals)

        if psi >= PSI_ALERT_THRESHOLD:
            severity = "alert"
        elif psi >= PSI_WARN_THRESHOLD:
            severity = "warn"
        else:
            severity = "ok"

        all_results.append({
            "feature": feature,
            "psi": round(psi, 4),
            "severity": severity,
        })

        # Log to database
        conn.execute(
            "INSERT INTO drift_log (run_date, feature_name, psi_value, severity) VALUES (?,?,?,?)",
            (run_date, feature, round(psi, 4), severity),
        )

        if severity != "ok":
            alerts.append({"feature": feature, "psi": round(psi, 4), "severity": severity})
            log_fn = logger.warning if severity == "alert" else logger.info
            log_fn(f"  Drift on {feature}: PSI={psi:.4f} ({severity})")

    conn.commit()

    # Summary
    if not alerts:
        logger.info("  No drift detected")
    else:
        logger.info(f"  {len(alerts)} feature(s) with drift")

    return alerts


def should_retrain_from_drift(alerts: List[Dict]) -> bool:
    """Determine if drift is severe enough to trigger retraining."""
    n_alerts = sum(1 for a in alerts if a["severity"] == "alert")
    return n_alerts >= DRIFT_RETRAIN_MIN_FEATURES


def get_drift_history(conn, n_days=30) -> pd.DataFrame:
    """Load drift log for visualization."""
    df = pd.read_sql("""
        SELECT run_date, feature_name, psi_value, severity
        FROM drift_log
        ORDER BY run_date DESC, feature_name
        LIMIT :limit
    """, conn, params={"limit": n_days * len(DRIFT_FEATURES)})
    return df


def _get_baseline_date():
    """Get the training date from the saved model artifact."""
    import joblib
    artifact_path = MODELS_DIR / "ranker_latest.pkl"
    if artifact_path.exists():
        try:
            artifact = joblib.load(artifact_path)
            return artifact.get("train_date")
        except Exception:
            pass
    return None


def _load_feature_snapshot(conn, reference_date):
    """Load customer features for a given reference date."""
    if reference_date is None:
        return None

    df = pd.read_sql(
        "SELECT * FROM customer_features",
        conn,
    )
    if df.empty:
        return None
    return df
