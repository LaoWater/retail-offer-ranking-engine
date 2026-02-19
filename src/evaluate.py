"""
Offline evaluation for Metro Personalized Offers Recommender.

Computes ranking quality metrics against historical redemptions:
  - NDCG@10, Precision@10, Recall@10, MRR, Redemption Rate@10

Also computes a random baseline for comparison.
"""

import logging
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from src.config import TOP_N_RECOMMENDATIONS, REDEMPTION_WINDOW_DAYS

logger = logging.getLogger(__name__)


def compute_offline_metrics(conn, run_date, k=None):
    """
    Evaluate recommendations against future redemptions.

    Args:
        conn: SQLite connection
        run_date: str, the date recommendations were generated
        k: int, cutoff for top-K metrics (default: TOP_N_RECOMMENDATIONS)

    Returns:
        dict of metric_name -> value
    """
    if k is None:
        k = TOP_N_RECOMMENDATIONS

    logger.info(f"Computing offline metrics for {run_date} (k={k})...")

    # Load recommendations
    recs = pd.read_sql("""
        SELECT customer_id, offer_id, rank
        FROM recommendations
        WHERE run_date = :rd
        ORDER BY customer_id, rank
    """, conn, params={"rd": run_date})

    if recs.empty:
        logger.warning("No recommendations found for %s", run_date)
        return {}

    # Load ground truth: redemptions in a window around run_date
    # Try forward window first; if it yields too few, use a backward window.
    # This handles the synthetic-data edge case where the pipeline runs near
    # the end of the generated history (almost no future redemptions exist).
    truth = pd.read_sql("""
        SELECT DISTINCT customer_id, offer_id
        FROM redemptions
        WHERE DATE(redeemed_timestamp) BETWEEN :rd AND DATE(:rd, '+' || :window || ' days')
    """, conn, params={"rd": run_date, "window": REDEMPTION_WINDOW_DAYS})

    if len(truth) < 50:
        # Fall back to lookback window — use the 30 days before run_date as ground truth
        logger.info(
            "  Forward window has only %d redemptions — using 30-day lookback window instead",
            len(truth),
        )
        truth = pd.read_sql("""
            SELECT DISTINCT customer_id, offer_id
            FROM redemptions
            WHERE DATE(redeemed_timestamp) BETWEEN DATE(:rd, '-30 days') AND :rd
        """, conn, params={"rd": run_date})

    # Build truth lookup: customer_id -> set of redeemed offer_ids
    truth_map = defaultdict(set)
    for _, row in truth.iterrows():
        truth_map[row["customer_id"]].add(row["offer_id"])

    # Compute per-customer metrics
    ndcg_scores = []
    precisions = []
    recalls = []
    reciprocal_ranks = []

    for customer_id, group in recs.groupby("customer_id"):
        ranked = group.sort_values("rank").head(k)
        ranked_offers = ranked["offer_id"].tolist()
        relevant = truth_map.get(customer_id, set())

        # Binary relevance vector
        relevance = [1 if oid in relevant else 0 for oid in ranked_offers]

        # NDCG@k
        ndcg_scores.append(_ndcg_at_k(relevance, k))

        # Precision@k
        precisions.append(sum(relevance) / k)

        # Recall@k
        if len(relevant) > 0:
            recalls.append(sum(relevance) / len(relevant))
        else:
            recalls.append(0.0)

        # MRR (Mean Reciprocal Rank)
        rr = 0.0
        for i, r in enumerate(relevance):
            if r == 1:
                rr = 1.0 / (i + 1)
                break
        reciprocal_ranks.append(rr)

    # Aggregate
    n_customers = len(ndcg_scores)
    users_with_redemption = sum(1 for rr in reciprocal_ranks if rr > 0)

    metrics = {
        "ndcg_at_k": round(np.mean(ndcg_scores), 4) if ndcg_scores else 0.0,
        "precision_at_k": round(np.mean(precisions), 4) if precisions else 0.0,
        "recall_at_k": round(np.mean(recalls), 4) if recalls else 0.0,
        "mrr": round(np.mean(reciprocal_ranks), 4) if reciprocal_ranks else 0.0,
        "redemption_rate_at_k": (
            round(users_with_redemption / n_customers, 4) if n_customers > 0 else 0.0
        ),
        "n_customers_evaluated": n_customers,
        "n_customers_with_redemption": users_with_redemption,
        "k": k,
    }

    # Random baseline
    random_metrics = _compute_random_baseline(conn, run_date, k, truth_map)
    for key, val in random_metrics.items():
        metrics[f"random_{key}"] = val

    # Lift over random
    if random_metrics.get("ndcg_at_k", 0) > 0:
        metrics["ndcg_lift"] = round(
            metrics["ndcg_at_k"] / random_metrics["ndcg_at_k"], 2
        )
    if random_metrics.get("redemption_rate_at_k", 0) > 0:
        metrics["redemption_rate_lift"] = round(
            metrics["redemption_rate_at_k"] / random_metrics["redemption_rate_at_k"], 2
        )

    logger.info(f"  NDCG@{k}: {metrics['ndcg_at_k']:.4f}")
    logger.info(f"  Precision@{k}: {metrics['precision_at_k']:.4f}")
    logger.info(f"  Recall@{k}: {metrics['recall_at_k']:.4f}")
    logger.info(f"  MRR: {metrics['mrr']:.4f}")
    logger.info(f"  Redemption Rate@{k}: {metrics['redemption_rate_at_k']:.4f}")
    if "ndcg_lift" in metrics:
        logger.info(f"  NDCG lift over random: {metrics['ndcg_lift']:.2f}x")

    return metrics


def _ndcg_at_k(relevance, k):
    """Compute NDCG@k for a single ranked list."""
    dcg = 0.0
    for i, rel in enumerate(relevance[:k]):
        dcg += rel / math.log2(i + 2)  # i+2 because positions are 1-indexed

    # Ideal DCG: sort relevance descending
    ideal = sorted(relevance, reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal):
        idcg += rel / math.log2(i + 2)

    if idcg == 0:
        return 0.0
    return dcg / idcg


def _compute_random_baseline(conn, run_date, k, truth_map):
    """Compute metrics for a random recommendation baseline."""
    rng = np.random.default_rng(0)

    # Get all active offers
    active_offers = pd.read_sql("""
        SELECT offer_id FROM offers
        WHERE start_date <= :rd AND end_date >= :rd
    """, conn, params={"rd": run_date})["offer_id"].tolist()

    if not active_offers:
        return {"ndcg_at_k": 0.0, "redemption_rate_at_k": 0.0}

    # Get all customers who received recommendations
    customers = pd.read_sql("""
        SELECT DISTINCT customer_id FROM recommendations WHERE run_date = :rd
    """, conn, params={"rd": run_date})["customer_id"].tolist()

    ndcg_scores = []
    rr_count = 0

    for cid in customers:
        # Random top-k
        random_offers = rng.choice(
            active_offers, size=min(k, len(active_offers)), replace=False
        ).tolist()
        relevant = truth_map.get(cid, set())
        relevance = [1 if oid in relevant else 0 for oid in random_offers]

        ndcg_scores.append(_ndcg_at_k(relevance, k))
        if any(r == 1 for r in relevance):
            rr_count += 1

    return {
        "ndcg_at_k": round(np.mean(ndcg_scores), 4) if ndcg_scores else 0.0,
        "redemption_rate_at_k": (
            round(rr_count / len(customers), 4) if customers else 0.0
        ),
    }
