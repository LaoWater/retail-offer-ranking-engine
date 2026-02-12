"""Tests for candidate generation."""

import pytest
import pandas as pd

from src.features import build_customer_features, build_offer_features
from src.candidates import generate_candidate_pool
from src.config import CANDIDATE_POOL_SIZE


class TestCandidateGeneration:
    @pytest.fixture(autouse=True)
    def setup(self, conn, run_date):
        """Build features before candidate tests."""
        build_customer_features(conn, run_date)
        build_offer_features(conn, run_date)

    def test_generates_candidates(self, conn, run_date):
        generate_candidate_pool(conn, run_date)
        count = conn.execute(
            "SELECT COUNT(*) FROM candidate_pool WHERE run_date = ?", (run_date,)
        ).fetchone()[0]
        assert count > 0, "Should generate candidates"

    def test_pool_size_capped(self, conn, run_date):
        generate_candidate_pool(conn, run_date)
        max_per_customer = pd.read_sql("""
            SELECT customer_id, COUNT(*) AS n
            FROM candidate_pool WHERE run_date = ?
            GROUP BY customer_id
        """, conn, params=(run_date,))

        assert (max_per_customer["n"] <= CANDIDATE_POOL_SIZE).all(), \
            f"No customer should have more than {CANDIDATE_POOL_SIZE} candidates"

    def test_no_duplicate_pairs(self, conn, run_date):
        generate_candidate_pool(conn, run_date)
        df = pd.read_sql(
            "SELECT customer_id, offer_id FROM candidate_pool WHERE run_date = ?",
            conn, params=(run_date,),
        )
        duplicates = df.duplicated(subset=["customer_id", "offer_id"])
        assert not duplicates.any(), "No duplicate (customer, offer) pairs"

    def test_strategies_labeled(self, conn, run_date):
        generate_candidate_pool(conn, run_date)
        strategies = pd.read_sql(
            "SELECT DISTINCT strategy FROM candidate_pool WHERE run_date = ?",
            conn, params=(run_date,),
        )["strategy"].tolist()

        assert len(strategies) > 0, "Should have at least one strategy"
        valid_strategies = {
            "category_affinity", "segment_popular", "repeat_purchase", "high_margin"
        }
        for s in strategies:
            assert s in valid_strategies, f"Unknown strategy: {s}"

    def test_idempotent(self, conn, run_date):
        """Running twice should produce the same result (not duplicate rows)."""
        generate_candidate_pool(conn, run_date)
        count1 = conn.execute(
            "SELECT COUNT(*) FROM candidate_pool WHERE run_date = ?", (run_date,)
        ).fetchone()[0]

        generate_candidate_pool(conn, run_date)
        count2 = conn.execute(
            "SELECT COUNT(*) FROM candidate_pool WHERE run_date = ?", (run_date,)
        ).fetchone()[0]

        assert count1 == count2, "Candidate generation should be idempotent"
