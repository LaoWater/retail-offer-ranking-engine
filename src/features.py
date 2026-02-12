"""
Feature engineering for Metro Personalized Offers Recommender.

Builds three feature tables:
  - customer_features: RFM, promo affinity, category entropy
  - offer_features: discount depth, margin impact, historical rates
  - interaction features: computed on-demand for (customer, offer) pairs
"""

import json
import logging
import math
from collections import defaultdict

import numpy as np
import pandas as pd

from src.config import CATEGORY_NAMES, SEGMENT_PROFILES, FEATURE_COLUMNS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Customer features
# ---------------------------------------------------------------------------

def build_customer_features(conn, reference_date):
    """
    Build customer_features table from orders, order_items, and customer data.

    Features (90-day lookback):
      - recency_days, frequency, monetary (RFM)
      - promo_affinity, avg_basket_size, avg_discount_depth
      - category_entropy, top_3_categories
      - loyalty_tier, segment
    """
    logger.info("Building customer features...")
    conn.execute("DROP TABLE IF EXISTS customer_features")

    # Core RFM + aggregates via SQL
    conn.execute("""
        CREATE TABLE customer_features AS
        WITH order_stats AS (
            SELECT
                o.customer_id,
                JULIANDAY(:ref) - MAX(JULIANDAY(o.order_timestamp)) AS recency_days,
                COUNT(DISTINCT o.order_id) AS frequency,
                SUM(o.total_amount) AS monetary,
                AVG(o.num_items) AS avg_basket_size
            FROM orders o
            WHERE JULIANDAY(o.order_timestamp) <= JULIANDAY(:ref)
              AND JULIANDAY(o.order_timestamp) > JULIANDAY(:ref) - 90
            GROUP BY o.customer_id
        ),
        promo_stats AS (
            SELECT
                o.customer_id,
                CAST(SUM(oi.is_promo) AS REAL) / MAX(COUNT(*), 1) AS promo_affinity,
                AVG(
                    CASE WHEN oi.is_promo = 1
                         THEN oi.discount_amount / MAX(oi.unit_price, 0.01)
                         ELSE NULL
                    END
                ) AS avg_discount_depth
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE JULIANDAY(o.order_timestamp) <= JULIANDAY(:ref)
              AND JULIANDAY(o.order_timestamp) > JULIANDAY(:ref) - 90
            GROUP BY o.customer_id
        )
        SELECT
            c.customer_id,
            COALESCE(os.recency_days, 999.0) AS recency_days,
            COALESCE(os.frequency, 0) AS frequency,
            COALESCE(os.monetary, 0.0) AS monetary,
            COALESCE(ps.promo_affinity, 0.0) AS promo_affinity,
            COALESCE(os.avg_basket_size, 0.0) AS avg_basket_size,
            0.0 AS category_entropy,
            '[]' AS top_3_categories,
            COALESCE(ps.avg_discount_depth, 0.0) AS avg_discount_depth,
            c.loyalty_tier,
            c.segment,
            :ref AS reference_date
        FROM customers c
        LEFT JOIN order_stats os ON c.customer_id = os.customer_id
        LEFT JOIN promo_stats ps ON c.customer_id = ps.customer_id
    """, {"ref": reference_date})
    conn.commit()

    # Post-process: category entropy and top-3 categories (requires Python)
    _compute_category_features(conn, reference_date)

    count = conn.execute("SELECT COUNT(*) FROM customer_features").fetchone()[0]
    logger.info(f"  customer_features: {count:,} rows")


def _compute_category_features(conn, reference_date):
    """Compute Shannon entropy and top-3 categories per customer."""
    cursor = conn.execute("""
        SELECT o.customer_id, p.category, COUNT(*) as cnt
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE JULIANDAY(o.order_timestamp) <= JULIANDAY(:ref)
          AND JULIANDAY(o.order_timestamp) > JULIANDAY(:ref) - 90
        GROUP BY o.customer_id, p.category
    """, {"ref": reference_date})

    # Accumulate per-customer category counts
    cust_cats = defaultdict(lambda: defaultdict(int))
    for row in cursor:
        cust_cats[row[0]][row[1]] += row[2]

    # Batch update
    updates = []
    for cid, cat_counts in cust_cats.items():
        total = sum(cat_counts.values())
        if total == 0:
            continue

        # Shannon entropy
        entropy = 0.0
        for cnt in cat_counts.values():
            p = cnt / total
            if p > 0:
                entropy -= p * math.log2(p)

        # Top 3 categories
        sorted_cats = sorted(cat_counts.items(), key=lambda x: -x[1])
        top3 = json.dumps([c[0] for c in sorted_cats[:3]])

        updates.append((entropy, top3, cid))

    conn.executemany(
        "UPDATE customer_features SET category_entropy = ?, top_3_categories = ? WHERE customer_id = ?",
        updates,
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Offer features
# ---------------------------------------------------------------------------

def build_offer_features(conn, reference_date):
    """
    Build offer_features table for active offers.

    Features:
      - discount_depth, margin_impact, days_until_expiry
      - historical_redemption_rate, total_impressions, total_redemptions
      - category, brand, base_price
    """
    logger.info("Building offer features...")
    conn.execute("DROP TABLE IF EXISTS offer_features")

    conn.execute("""
        CREATE TABLE offer_features AS
        SELECT
            o.offer_id,
            CASE o.discount_type
                WHEN 'percentage' THEN o.discount_value / 100.0
                WHEN 'fixed_amount' THEN MIN(1.0, o.discount_value / MAX(p.base_price, 0.01))
                WHEN 'bogo' THEN 0.50
            END AS discount_depth,
            p.base_price * COALESCE(p.margin, 0.15) * (
                CASE o.discount_type
                    WHEN 'percentage' THEN o.discount_value / 100.0
                    WHEN 'fixed_amount' THEN MIN(1.0, o.discount_value / MAX(p.base_price, 0.01))
                    WHEN 'bogo' THEN 0.50
                END
            ) AS margin_impact,
            CAST(MAX(0, JULIANDAY(o.end_date) - JULIANDAY(:ref)) AS INTEGER) AS days_until_expiry,
            COALESCE(
                CAST(red_counts.cnt AS REAL) / MAX(imp_counts.cnt, 1),
                0.0
            ) AS historical_redemption_rate,
            COALESCE(imp_counts.cnt, 0) AS total_impressions,
            COALESCE(red_counts.cnt, 0) AS total_redemptions,
            p.category,
            p.brand,
            p.base_price,
            :ref AS reference_date
        FROM offers o
        JOIN products p ON o.product_id = p.product_id
        LEFT JOIN (
            SELECT offer_id, COUNT(*) AS cnt
            FROM impressions
            WHERE JULIANDAY(shown_timestamp) <= JULIANDAY(:ref)
            GROUP BY offer_id
        ) imp_counts ON o.offer_id = imp_counts.offer_id
        LEFT JOIN (
            SELECT offer_id, COUNT(*) AS cnt
            FROM redemptions
            WHERE JULIANDAY(redeemed_timestamp) <= JULIANDAY(:ref)
            GROUP BY offer_id
        ) red_counts ON o.offer_id = red_counts.offer_id
    """, {"ref": reference_date})
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM offer_features").fetchone()[0]
    logger.info(f"  offer_features: {count:,} rows")


# ---------------------------------------------------------------------------
# Interaction features (computed on-demand for pairs)
# ---------------------------------------------------------------------------

def build_interaction_features(conn, pairs_df, reference_date):
    """
    Compute interaction features for given (customer_id, offer_id) pairs.

    Args:
        conn: SQLite connection
        pairs_df: DataFrame with columns ['customer_id', 'offer_id']
        reference_date: str, date for time-relative features

    Returns:
        DataFrame with columns:
            customer_id, offer_id, bought_product_before,
            days_since_last_cat_purchase, category_affinity_score,
            discount_depth_vs_usual, price_sensitivity_match
    """
    if pairs_df.empty:
        return pd.DataFrame(columns=[
            "customer_id", "offer_id", "bought_product_before",
            "days_since_last_cat_purchase", "category_affinity_score",
            "discount_depth_vs_usual", "price_sensitivity_match",
        ])

    logger.info(f"Computing interaction features for {len(pairs_df):,} pairs...")

    # ---- Pre-compute lookups ----

    # 1) offer -> (product_id, category)
    offer_info = pd.read_sql("""
        SELECT o.offer_id, o.product_id, p.category,
               CASE o.discount_type
                   WHEN 'percentage' THEN o.discount_value / 100.0
                   WHEN 'fixed_amount' THEN MIN(1.0, o.discount_value / MAX(p.base_price, 0.01))
                   WHEN 'bogo' THEN 0.50
               END AS discount_depth
        FROM offers o
        JOIN products p ON o.product_id = p.product_id
    """, conn)
    offer_map = offer_info.set_index("offer_id")

    # 2) customer -> set of purchased product_ids
    cust_products_raw = pd.read_sql("""
        SELECT DISTINCT o.customer_id, oi.product_id
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE JULIANDAY(o.order_timestamp) <= JULIANDAY(:ref)
    """, conn, params={"ref": reference_date})
    cust_products = defaultdict(set)
    for _, row in cust_products_raw.iterrows():
        cust_products[row["customer_id"]].add(row["product_id"])

    # 3) customer -> (category -> last_purchase_date)
    cat_recency_raw = pd.read_sql("""
        SELECT o.customer_id, p.category,
               MAX(DATE(o.order_timestamp)) AS last_date
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE JULIANDAY(o.order_timestamp) <= JULIANDAY(:ref)
        GROUP BY o.customer_id, p.category
    """, conn, params={"ref": reference_date})
    cust_cat_recency = defaultdict(dict)
    for _, row in cat_recency_raw.iterrows():
        cust_cat_recency[row["customer_id"]][row["category"]] = row["last_date"]

    # 4) customer -> (category -> purchase_count) for affinity
    cat_counts_raw = pd.read_sql("""
        SELECT o.customer_id, p.category, COUNT(*) AS cnt
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE JULIANDAY(o.order_timestamp) <= JULIANDAY(:ref)
        GROUP BY o.customer_id, p.category
    """, conn, params={"ref": reference_date})
    cust_cat_counts = defaultdict(lambda: defaultdict(int))
    cust_total_items = defaultdict(int)
    for _, row in cat_counts_raw.iterrows():
        cust_cat_counts[row["customer_id"]][row["category"]] = row["cnt"]
        cust_total_items[row["customer_id"]] += row["cnt"]

    # 5) customer features for discount comparison
    cust_feats = pd.read_sql(
        "SELECT customer_id, avg_discount_depth, segment FROM customer_features",
        conn,
    )
    cust_feat_map = cust_feats.set_index("customer_id")

    # ---- Compute features ----
    from datetime import date as dt_date
    ref_date = dt_date.fromisoformat(reference_date)
    ref_julian = ref_date.toordinal()

    results = []
    for _, pair in pairs_df.iterrows():
        cid = pair["customer_id"]
        oid = pair["offer_id"]

        # Get offer info
        if oid not in offer_map.index:
            results.append({
                "customer_id": cid, "offer_id": oid,
                "bought_product_before": 0, "days_since_last_cat_purchase": 999,
                "category_affinity_score": 0.0, "discount_depth_vs_usual": 0.0,
                "price_sensitivity_match": 0.0,
            })
            continue

        o_info = offer_map.loc[oid]
        prod_id = o_info["product_id"]
        cat = o_info["category"]
        off_depth = o_info["discount_depth"]

        # bought_product_before
        bought_before = 1 if prod_id in cust_products.get(cid, set()) else 0

        # days_since_last_cat_purchase
        last_cat_date = cust_cat_recency.get(cid, {}).get(cat)
        if last_cat_date:
            try:
                last_ord = dt_date.fromisoformat(last_cat_date).toordinal()
                days_since = ref_julian - last_ord
            except (ValueError, TypeError):
                days_since = 999
        else:
            days_since = 999

        # category_affinity_score
        total = cust_total_items.get(cid, 0)
        cat_cnt = cust_cat_counts.get(cid, {}).get(cat, 0)
        affinity = cat_cnt / max(total, 1)

        # discount_depth_vs_usual
        cust_avg_depth = 0.0
        segment = "budget"
        if cid in cust_feat_map.index:
            row = cust_feat_map.loc[cid]
            cust_avg_depth = row["avg_discount_depth"] if pd.notna(row["avg_discount_depth"]) else 0.0
            segment = row["segment"] if pd.notna(row["segment"]) else "budget"
        depth_vs_usual = off_depth - cust_avg_depth

        # price_sensitivity_match
        sensitivity = SEGMENT_PROFILES.get(segment, {}).get("price_sensitivity", 0.5)
        psm = sensitivity * off_depth

        results.append({
            "customer_id": cid,
            "offer_id": oid,
            "bought_product_before": bought_before,
            "days_since_last_cat_purchase": days_since,
            "category_affinity_score": round(affinity, 4),
            "discount_depth_vs_usual": round(depth_vs_usual, 4),
            "price_sensitivity_match": round(psm, 4),
        })

    df = pd.DataFrame(results)
    logger.info(f"  Interaction features computed: {len(df):,} rows")
    return df
