"""Tests for feature engineering."""

import pytest
import pandas as pd

from src.features import (
    build_customer_features,
    build_offer_features,
    build_interaction_features,
)


class TestCustomerFeatures:
    def test_builds_successfully(self, conn, run_date):
        build_customer_features(conn, run_date)
        count = conn.execute("SELECT COUNT(*) FROM customer_features").fetchone()[0]
        assert count > 0, "customer_features should have rows"

    def test_has_expected_columns(self, conn, run_date):
        build_customer_features(conn, run_date)
        cursor = conn.execute("PRAGMA table_info(customer_features)")
        columns = {row[1] for row in cursor}
        expected = {
            "customer_id", "recency_days", "frequency", "monetary",
            "promo_affinity", "avg_basket_size", "category_entropy",
            "top_3_categories", "avg_discount_depth", "loyalty_tier",
            "segment", "reference_date",
        }
        assert expected.issubset(columns)

    def test_recency_nonnegative(self, conn, run_date):
        build_customer_features(conn, run_date)
        df = pd.read_sql("SELECT recency_days FROM customer_features", conn)
        assert (df["recency_days"] >= 0).all(), "Recency should be >= 0"

    def test_frequency_nonnegative(self, conn, run_date):
        build_customer_features(conn, run_date)
        df = pd.read_sql("SELECT frequency FROM customer_features", conn)
        assert (df["frequency"] >= 0).all(), "Frequency should be >= 0"

    def test_monetary_nonnegative(self, conn, run_date):
        build_customer_features(conn, run_date)
        df = pd.read_sql("SELECT monetary FROM customer_features", conn)
        assert (df["monetary"] >= 0).all(), "Monetary should be >= 0"

    def test_promo_affinity_bounded(self, conn, run_date):
        build_customer_features(conn, run_date)
        df = pd.read_sql("SELECT promo_affinity FROM customer_features", conn)
        assert (df["promo_affinity"] >= 0).all()
        assert (df["promo_affinity"] <= 1).all()

    def test_category_entropy_nonnegative(self, conn, run_date):
        build_customer_features(conn, run_date)
        df = pd.read_sql("SELECT category_entropy FROM customer_features", conn)
        assert (df["category_entropy"] >= 0).all()

    def test_all_customers_present(self, conn, run_date):
        build_customer_features(conn, run_date)
        n_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        n_features = conn.execute("SELECT COUNT(*) FROM customer_features").fetchone()[0]
        assert n_features == n_customers


class TestOfferFeatures:
    def test_builds_successfully(self, conn, run_date):
        build_offer_features(conn, run_date)
        count = conn.execute("SELECT COUNT(*) FROM offer_features").fetchone()[0]
        assert count > 0

    def test_discount_depth_bounded(self, conn, run_date):
        build_offer_features(conn, run_date)
        df = pd.read_sql("SELECT discount_depth FROM offer_features", conn)
        assert (df["discount_depth"] >= 0).all()
        assert (df["discount_depth"] <= 1.0).all()

    def test_days_until_expiry_nonnegative(self, conn, run_date):
        build_offer_features(conn, run_date)
        df = pd.read_sql("SELECT days_until_expiry FROM offer_features", conn)
        assert (df["days_until_expiry"] >= 0).all()


class TestInteractionFeatures:
    def test_returns_dataframe(self, conn, run_date):
        build_customer_features(conn, run_date)
        build_offer_features(conn, run_date)

        pairs = pd.DataFrame({
            "customer_id": [1, 2, 3],
            "offer_id": [1, 1, 2],
        })
        result = build_interaction_features(conn, pairs, run_date)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_has_expected_columns(self, conn, run_date):
        build_customer_features(conn, run_date)
        pairs = pd.DataFrame({"customer_id": [1], "offer_id": [1]})
        result = build_interaction_features(conn, pairs, run_date)
        expected = {
            "customer_id", "offer_id", "bought_product_before",
            "days_since_last_cat_purchase", "category_affinity_score",
            "discount_depth_vs_usual", "price_sensitivity_match",
        }
        assert expected.issubset(set(result.columns))

    def test_empty_pairs(self, conn, run_date):
        pairs = pd.DataFrame(columns=["customer_id", "offer_id"])
        result = build_interaction_features(conn, pairs, run_date)
        assert len(result) == 0
