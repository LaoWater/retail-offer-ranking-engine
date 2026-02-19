"""
Daily batch pipeline for Metro Personalized Offers Recommender.

Single-command orchestration of the entire recommendation pipeline:
  1. Build features
  2. Train or load model
  3. Generate candidates
  4. Score candidates
  5. Check drift
  6. Evaluate

Usage:
    python src/daily_run.py --date 2026-02-11
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import RETRAIN_DAY_OF_WEEK, MODELS_DIR
from src.db import get_connection
from src.simulate_day_behavior import simulate_day
from src.features import build_customer_features, build_offer_features
from src.candidates import generate_candidate_pool
from src.train_ranker import train_ranker, load_model
from src.score_ranker import score_candidates
from src.drift import check_drift, should_retrain_from_drift
from src.evaluate import compute_offline_metrics

logger = logging.getLogger(__name__)


def run_pipeline(run_date: str):
    """
    Execute the full daily recommendation pipeline.

    Args:
        run_date: str, date in YYYY-MM-DD format
    """
    conn = get_connection()
    pipeline_start = time.time()

    logger.info("=" * 60)
    logger.info(f"DAILY PIPELINE - {run_date}")
    logger.info("=" * 60)

    results = {}

    # ---- Step 0: Simulate day behavior ----
    _run_step(conn, run_date, "behavior",
              lambda: simulate_day(conn, run_date),
              results)

    # ---- Step 1: Build features ----
    _run_step(conn, run_date, "features", lambda: _step_features(conn, run_date), results)

    # ---- Step 2: Train or load model ----
    model = _run_step(conn, run_date, "model", lambda: _step_model(conn, run_date), results)

    if model is None:
        logger.error("No model available. Aborting pipeline.")
        conn.close()
        return results

    # ---- Step 3: Generate candidates ----
    _run_step(conn, run_date, "candidates", lambda: _step_candidates(conn, run_date), results)

    # ---- Step 4: Score candidates ----
    _run_step(conn, run_date, "scoring", lambda: _step_scoring(model, run_date, conn), results)

    # ---- Step 5: Drift detection ----
    _run_step(conn, run_date, "drift", lambda: _step_drift(conn, run_date), results)

    # ---- Step 6: Evaluation ----
    _run_step(conn, run_date, "evaluate", lambda: _step_evaluate(conn, run_date), results)

    # ---- Summary ----
    total_time = time.time() - pipeline_start
    logger.info("=" * 60)
    logger.info(f"Pipeline completed in {total_time:.1f}s")
    for step, info in results.items():
        status = info.get("status", "unknown")
        duration = info.get("duration", 0)
        logger.info(f"  {step:15s}: {status:10s} ({duration:.1f}s)")
    logger.info("=" * 60)

    conn.close()
    return results


def _run_step(conn, run_date, step_name, step_fn, results):
    """Execute a pipeline step with timing and error handling."""
    logger.info(f"\n--- Step: {step_name} ---")
    _log_pipeline_run(conn, run_date, step_name, "started")

    t0 = time.time()
    try:
        result = step_fn()
        duration = time.time() - t0
        # Serialize dict results (e.g. evaluate metrics) as JSON metadata
        metadata = json.dumps(result) if isinstance(result, dict) else None
        _log_pipeline_run(conn, run_date, step_name, "completed", duration, metadata)
        results[step_name] = {"status": "completed", "duration": duration, "result": result}
        logger.info(f"  Completed in {duration:.1f}s")
        return result
    except Exception as e:
        duration = time.time() - t0
        _log_pipeline_run(conn, run_date, step_name, "failed", duration, str(e))
        results[step_name] = {"status": "failed", "duration": duration, "error": str(e)}
        logger.exception(f"  FAILED: {e}")
        return None


def _step_features(conn, run_date):
    build_customer_features(conn, run_date)
    build_offer_features(conn, run_date)


def _step_model(conn, run_date):
    """Train a new model or load existing one based on schedule."""
    dt = datetime.strptime(run_date, "%Y-%m-%d")
    artifact_path = MODELS_DIR / "ranker_latest.pkl"
    should_train = (
        dt.weekday() == RETRAIN_DAY_OF_WEEK
        or not artifact_path.exists()
    )

    if should_train:
        logger.info("Training new model...")
        model, metrics = train_ranker(conn, run_date)
        return model
    else:
        logger.info("Loading existing model...")
        model, _ = load_model()
        return model


def _step_candidates(conn, run_date):
    generate_candidate_pool(conn, run_date)


def _step_scoring(model, run_date, conn):
    return score_candidates(model, run_date, conn)


def _step_drift(conn, run_date):
    alerts = check_drift(conn, run_date)
    if should_retrain_from_drift(alerts):
        logger.warning("Drift-triggered retraining recommended!")
    return alerts


def _step_evaluate(conn, run_date):
    return compute_offline_metrics(conn, run_date)


def _log_pipeline_run(conn, run_date, step, status, duration=None, metadata=None):
    """Log pipeline step to pipeline_runs table."""
    conn.execute(
        "INSERT INTO pipeline_runs (run_date, step, status, duration_seconds, metadata) VALUES (?,?,?,?,?)",
        (run_date, step, status, duration, metadata),
    )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Metro daily recommendation pipeline")
    parser.add_argument("--date", required=True, help="Run date (YYYY-MM-DD)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    run_pipeline(args.date)


if __name__ == "__main__":
    main()
