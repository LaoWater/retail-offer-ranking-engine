"""
Feature engineering for Metro Romania Personalized Offers Recommender.

Builds three feature tables:
  - customer_features: RFM, tier purchase ratios, fresh ratio, promo affinity
  - offer_features: discount depth, margin impact, own brand, segment rates
  - interaction features: computed on-demand for (customer, offer) pairs
"""

import json
import logging
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from src.config import CATEGORY_NAMES, BUSINESS_PROFILES, FEATURE_COLUMNS, FRESH_CATEGORIES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Customer features
# ---------------------------------------------------------------------------

def build_customer_features(conn, reference_date):
    """
    Build customer_features table from orders, order_items, and customer data.

    Features (90-day lookback):
      - recency_days, frequency, monetary (RFM)
      - promo_affinity, avg_basket_size, avg_basket_quantity, avg_order_value
      - avg_discount_depth
      - tier2_purchase_ratio, tier3_purchase_ratio, avg_tier_savings_pct
      - fresh_category_ratio, business_order_ratio
      - category_entropy, top_3_categories
      - preferred_shopping_day, days_between_visits_avg
      - loyalty_tier, business_type, business_subtype
    """
    logger.info("Building customer features...")
    conn.execute("DROP TABLE IF EXISTS customer_features")

    conn.execute("""
        CREATE TABLE customer_features AS
        WITH order_stats AS (
            SELECT
                o.customer_id,
                JULIANDAY(:ref) - MAX(JULIANDAY(o.order_timestamp)) AS recency_days,
                COUNT(DISTINCT o.order_id) AS frequency,
                SUM(o.total_amount) AS monetary,
                AVG(o.num_items) AS avg_basket_size,
                AVG(o.total_quantity) AS avg_basket_quantity,
                AVG(o.total_amount) AS avg_order_value
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
        ),
        tier_stats AS (
            SELECT
                o.customer_id,
                CAST(SUM(CASE WHEN oi.tier_applied = 2 THEN 1 ELSE 0 END) AS REAL)
                    / MAX(COUNT(*), 1) AS tier2_purchase_ratio,
                CAST(SUM(CASE WHEN oi.tier_applied = 3 THEN 1 ELSE 0 END) AS REAL)
                    / MAX(COUNT(*), 1) AS tier3_purchase_ratio,
                AVG(
                    CASE WHEN oi.tier_savings > 0
                         THEN oi.tier_savings / MAX(oi.unit_price + oi.tier_savings, 0.01)
                         ELSE 0.0
                    END
                ) AS avg_tier_savings_pct
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE JULIANDAY(o.order_timestamp) <= JULIANDAY(:ref)
              AND JULIANDAY(o.order_timestamp) > JULIANDAY(:ref) - 90
            GROUP BY o.customer_id
        ),
        fresh_stats AS (
            SELECT
                o.customer_id,
                CAST(SUM(CASE WHEN p.category IN ('meat_poultry','dairy_eggs','fruits_vegetables','bakery_pastry','seafood','deli_charcuterie') THEN 1 ELSE 0 END) AS REAL)
                    / MAX(COUNT(*), 1) AS fresh_category_ratio
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE JULIANDAY(o.order_timestamp) <= JULIANDAY(:ref)
              AND JULIANDAY(o.order_timestamp) > JULIANDAY(:ref) - 90
            GROUP BY o.customer_id
        ),
        purchase_mode_stats AS (
            SELECT
                o.customer_id,
                CAST(SUM(CASE WHEN o.purchase_mode = 'business' THEN 1 ELSE 0 END) AS REAL)
                    / MAX(COUNT(*), 1) AS business_order_ratio
            FROM orders o
            WHERE JULIANDAY(o.order_timestamp) <= JULIANDAY(:ref)
              AND JULIANDAY(o.order_timestamp) > JULIANDAY(:ref) - 90
            GROUP BY o.customer_id
        ),
        visit_pattern AS (
            SELECT
                o.customer_id,
                CAST(
                    (SELECT CAST(strftime('%w', sub.order_timestamp) AS INTEGER)
                     FROM orders sub
                     WHERE sub.customer_id = o.customer_id
                       AND JULIANDAY(sub.order_timestamp) <= JULIANDAY(:ref)
                       AND JULIANDAY(sub.order_timestamp) > JULIANDAY(:ref) - 90
                     GROUP BY CAST(strftime('%w', sub.order_timestamp) AS INTEGER)
                     ORDER BY COUNT(*) DESC
                     LIMIT 1
                    ) AS INTEGER
                ) AS preferred_shopping_day
            FROM customers o
        )
        SELECT
            c.customer_id,
            COALESCE(os.recency_days, 999.0) AS recency_days,
            COALESCE(os.frequency, 0) AS frequency,
            COALESCE(os.monetary, 0.0) AS monetary,
            COALESCE(ps.promo_affinity, 0.0) AS promo_affinity,
            COALESCE(os.avg_basket_size, 0.0) AS avg_basket_size,
            COALESCE(os.avg_basket_quantity, 0.0) AS avg_basket_quantity,
            COALESCE(os.avg_order_value, 0.0) AS avg_order_value,
            0.0 AS category_entropy,
            '[]' AS top_3_categories,
            COALESCE(ps.avg_discount_depth, 0.0) AS avg_discount_depth,
            COALESCE(ts.tier2_purchase_ratio, 0.0) AS tier2_purchase_ratio,
            COALESCE(ts.tier3_purchase_ratio, 0.0) AS tier3_purchase_ratio,
            COALESCE(ts.avg_tier_savings_pct, 0.0) AS avg_tier_savings_pct,
            COALESCE(fs.fresh_category_ratio, 0.0) AS fresh_category_ratio,
            COALESCE(pm.business_order_ratio, 1.0) AS business_order_ratio,
            vp.preferred_shopping_day,
            CASE WHEN os.frequency > 1
                 THEN COALESCE(os.recency_days, 90.0) / MAX(os.frequency - 1, 1)
                 ELSE NULL
            END AS days_between_visits_avg,
            c.loyalty_tier,
            c.business_type,
            c.business_subtype,
            :ref AS reference_date
        FROM customers c
        LEFT JOIN order_stats os ON c.customer_id = os.customer_id
        LEFT JOIN promo_stats ps ON c.customer_id = ps.customer_id
        LEFT JOIN tier_stats ts ON c.customer_id = ts.customer_id
        LEFT JOIN fresh_stats fs ON c.customer_id = fs.customer_id
        LEFT JOIN purchase_mode_stats pm ON c.customer_id = pm.customer_id
        LEFT JOIN visit_pattern vp ON c.customer_id = vp.customer_id
    """, {"ref": reference_date})
    conn.commit()

    # Post-process: category entropy and top-3 categories
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

    cust_cats = defaultdict(lambda: defaultdict(int))
    for row in cursor:
        cust_cats[row[0]][row[1]] += row[2]

    updates = []
    for cid, cat_counts in cust_cats.items():
        total = sum(cat_counts.values())
        if total == 0:
            continue

        entropy = 0.0
        for cnt in cat_counts.values():
            p = cnt / total
            if p > 0:
                entropy -= p * math.log2(p)

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
      - category, brand, tier1_price, is_own_brand
      - offer_type, campaign_type
      - horeca_redemption_rate, trader_redemption_rate
    """
    logger.info("Building offer features...")
    conn.execute("DROP TABLE IF EXISTS offer_features")

    conn.execute("""
        CREATE TABLE offer_features AS
        SELECT
            o.offer_id,
            CASE o.offer_type
                WHEN 'percentage' THEN o.discount_value / 100.0
                WHEN 'fixed_amount' THEN MIN(1.0, o.discount_value / MAX(p.tier1_price, 0.01))
                WHEN 'buy_x_get_y' THEN 0.50
                WHEN 'volume_bonus' THEN o.discount_value / 100.0
                WHEN 'bundle' THEN 0.30
                WHEN 'free_gift' THEN 0.20
            END AS discount_depth,
            p.tier1_price * COALESCE(p.margin, 0.15) * (
                CASE o.offer_type
                    WHEN 'percentage' THEN o.discount_value / 100.0
                    WHEN 'fixed_amount' THEN MIN(1.0, o.discount_value / MAX(p.tier1_price, 0.01))
                    WHEN 'buy_x_get_y' THEN 0.50
                    WHEN 'volume_bonus' THEN o.discount_value / 100.0
                    WHEN 'bundle' THEN 0.30
                    WHEN 'free_gift' THEN 0.20
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
            p.tier1_price,
            p.is_own_brand,
            o.offer_type,
            o.campaign_type,
            COALESCE(horeca_red.rate, 0.0) AS horeca_redemption_rate,
            COALESCE(trader_red.rate, 0.0) AS trader_redemption_rate,
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
        LEFT JOIN (
            SELECT r.offer_id,
                   CAST(COUNT(*) AS REAL) / MAX(
                       (SELECT COUNT(*) FROM impressions i2
                        JOIN customers c2 ON i2.customer_id = c2.customer_id
                        WHERE i2.offer_id = r.offer_id AND c2.business_type = 'horeca'), 1
                   ) AS rate
            FROM redemptions r
            JOIN customers c ON r.customer_id = c.customer_id
            WHERE c.business_type = 'horeca'
              AND JULIANDAY(r.redeemed_timestamp) <= JULIANDAY(:ref)
            GROUP BY r.offer_id
        ) horeca_red ON o.offer_id = horeca_red.offer_id
        LEFT JOIN (
            SELECT r.offer_id,
                   CAST(COUNT(*) AS REAL) / MAX(
                       (SELECT COUNT(*) FROM impressions i2
                        JOIN customers c2 ON i2.customer_id = c2.customer_id
                        WHERE i2.offer_id = r.offer_id AND c2.business_type = 'trader'), 1
                   ) AS rate
            FROM redemptions r
            JOIN customers c ON r.customer_id = c.customer_id
            WHERE c.business_type = 'trader'
              AND JULIANDAY(r.redeemed_timestamp) <= JULIANDAY(:ref)
            GROUP BY r.offer_id
        ) trader_red ON o.offer_id = trader_red.offer_id
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

    Returns:
        DataFrame with columns:
            customer_id, offer_id, bought_product_before,
            days_since_last_cat_purchase, category_affinity_score,
            discount_depth_vs_usual, price_sensitivity_match,
            business_type_match
    """
    if pairs_df.empty:
        return pd.DataFrame(columns=[
            "customer_id", "offer_id", "bought_product_before",
            "days_since_last_cat_purchase", "category_affinity_score",
            "discount_depth_vs_usual", "price_sensitivity_match",
            "business_type_match",
        ])

    logger.info(f"Computing interaction features for {len(pairs_df):,} pairs...")

    # ---- Pre-compute lookups ----

    # 1) offer -> (product_id, category, discount_depth)
    offer_info = pd.read_sql("""
        SELECT o.offer_id, o.product_id, p.category,
               CASE o.offer_type
                   WHEN 'percentage' THEN o.discount_value / 100.0
                   WHEN 'fixed_amount' THEN MIN(1.0, o.discount_value / MAX(p.tier1_price, 0.01))
                   WHEN 'buy_x_get_y' THEN 0.50
                   WHEN 'volume_bonus' THEN o.discount_value / 100.0
                   WHEN 'bundle' THEN 0.30
                   WHEN 'free_gift' THEN 0.20
               END AS discount_depth,
               o.business_type_scope
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

    # 5) customer features for discount comparison and business type
    cust_feats = pd.read_sql(
        "SELECT customer_id, avg_discount_depth, business_type FROM customer_features",
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

        if oid not in offer_map.index:
            results.append({
                "customer_id": cid, "offer_id": oid,
                "bought_product_before": 0, "days_since_last_cat_purchase": 999,
                "category_affinity_score": 0.0, "discount_depth_vs_usual": 0.0,
                "price_sensitivity_match": 0.0, "business_type_match": 0.0,
            })
            continue

        o_info = offer_map.loc[oid]
        prod_id = o_info["product_id"]
        cat = o_info["category"]
        off_depth = o_info["discount_depth"]
        bt_scope = o_info["business_type_scope"]

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
        business_type = "horeca"
        if cid in cust_feat_map.index:
            row = cust_feat_map.loc[cid]
            cust_avg_depth = row["avg_discount_depth"] if pd.notna(row["avg_discount_depth"]) else 0.0
            business_type = row["business_type"] if pd.notna(row["business_type"]) else "horeca"
        depth_vs_usual = off_depth - cust_avg_depth

        # price_sensitivity_match
        # Find the first matching subtype profile for this business type
        sensitivity = 0.5
        for sub_name, profile in BUSINESS_PROFILES.items():
            # Use a rough matching — get from cust_feat_map if possible
            if cid in cust_feat_map.index:
                # We only have business_type in the feature map, not subtype
                # Use average sensitivity for the business type
                pass
            break
        # Approximate: use business type average
        bt_subtypes = [s for s in BUSINESS_PROFILES if True]  # all subtypes
        if cid in cust_feat_map.index:
            bt = cust_feat_map.loc[cid]["business_type"]
            if pd.notna(bt):
                bt_profiles = [
                    BUSINESS_PROFILES[s]["price_sensitivity"]
                    for s in BUSINESS_PROFILES
                ]
                sensitivity = np.mean(bt_profiles)
        psm = sensitivity * off_depth

        # business_type_match: does the offer target this customer's business type?
        bt_match = 1.0
        if pd.notna(bt_scope) and bt_scope:
            bt_match = 1.0 if business_type in str(bt_scope).split(",") else 0.0

        results.append({
            "customer_id": cid,
            "offer_id": oid,
            "bought_product_before": bought_before,
            "days_since_last_cat_purchase": days_since,
            "category_affinity_score": round(affinity, 4),
            "discount_depth_vs_usual": round(depth_vs_usual, 4),
            "price_sensitivity_match": round(psm, 4),
            "business_type_match": bt_match,
        })

    df = pd.DataFrame(results)
    logger.info(f"  Interaction features computed: {len(df):,} rows")
    return df
