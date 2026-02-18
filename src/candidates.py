"""
Candidate generation for Metro Romania Personalized Offers Recommender.

Retrieves ~200 eligible offers per customer using 7 heuristic strategies:
  1. Category affinity (60 candidates)
  2. Business type popularity (40 candidates)
  3. Repeat purchase (30 candidates)
  4. High margin (20 candidates)
  5. Tier upgrade (20 candidates)
  6. Cross-sell (15 candidates)
  7. Own brand switch (15 candidates)

This is stage 1 of the two-stage recommender (retrieval -> ranking).
"""

import logging
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from src.config import CANDIDATE_POOL_SIZE, CANDIDATE_STRATEGY_LIMITS

logger = logging.getLogger(__name__)


def generate_candidate_pool(conn, run_date):
    """
    Generate candidate offers for all customers and write to candidate_pool table.
    """
    logger.info("Generating candidate pool...")

    conn.execute("DELETE FROM candidate_pool WHERE run_date = ?", (run_date,))
    conn.commit()

    # ---- Load reference data ----

    # Active offers on run_date
    active_offers = pd.read_sql("""
        SELECT o.offer_id, o.product_id, o.store_scope, o.business_type_scope,
               o.business_subtype_scope, o.loyalty_tier_scope,
               o.discount_value, o.offer_type,
               p.category, p.margin, p.tier1_price, p.is_own_brand
        FROM offers o
        JOIN products p ON o.product_id = p.product_id
        WHERE o.start_date <= :rd AND o.end_date >= :rd
    """, conn, params={"rd": run_date})

    if active_offers.empty:
        logger.warning("No active offers found for date %s", run_date)
        return

    logger.info(f"  Active offers: {len(active_offers)}")

    # Pre-build lookup structures
    cat_to_offers = defaultdict(list)
    for _, row in active_offers.iterrows():
        cat_to_offers[row["category"]].append(row["offer_id"])

    # High-margin strategy
    active_offers["effective_margin"] = (
        active_offers["tier1_price"] * active_offers["margin"]
    )
    high_margin_offers = (
        active_offers.nlargest(CANDIDATE_STRATEGY_LIMITS["high_margin"], "effective_margin")["offer_id"]
        .tolist()
    )

    # Own brand offers (for own_brand_switch strategy)
    own_brand_offers = active_offers[active_offers["is_own_brand"] == 1]["offer_id"].tolist()

    # Business type popularity: count impressions per offer per business_type
    bt_popularity = pd.read_sql("""
        SELECT c.business_type, i.offer_id, COUNT(*) AS imp_count
        FROM impressions i
        JOIN customers c ON i.customer_id = c.customer_id
        GROUP BY c.business_type, i.offer_id
    """, conn)
    bt_pop_map = defaultdict(list)
    for _, row in bt_popularity.iterrows():
        bt_pop_map[row["business_type"]].append((row["offer_id"], row["imp_count"]))
    for bt in bt_pop_map:
        bt_pop_map[bt].sort(key=lambda x: -x[1])

    # Customer data
    customers = pd.read_sql("""
        SELECT customer_id, business_type, business_subtype, home_store_id, loyalty_tier
        FROM customers
    """, conn)

    # Customer top categories from customer_features
    cust_top_cats = {}
    rows = conn.execute(
        "SELECT customer_id, top_3_categories FROM customer_features"
    ).fetchall()
    import json
    for row in rows:
        try:
            cats = json.loads(row[1]) if row[1] else []
        except (json.JSONDecodeError, TypeError):
            cats = []
        cust_top_cats[row[0]] = cats

    # Customer purchased products (last 90 days)
    cust_products_raw = pd.read_sql("""
        SELECT DISTINCT o.customer_id, oi.product_id
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE DATE(o.order_timestamp) >= DATE(:rd, '-90 days')
    """, conn, params={"rd": run_date})
    cust_products = defaultdict(set)
    for _, row in cust_products_raw.iterrows():
        cust_products[row["customer_id"]].add(row["product_id"])

    # Customer purchased categories (for cross-sell)
    cust_purchased_cats = defaultdict(set)
    cat_raw = pd.read_sql("""
        SELECT DISTINCT o.customer_id, p.category
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE DATE(o.order_timestamp) >= DATE(:rd, '-90 days')
    """, conn, params={"rd": run_date})
    for _, row in cat_raw.iterrows():
        cust_purchased_cats[row["customer_id"]].add(row["category"])

    # Customer tier behavior (for tier_upgrade strategy)
    cust_tier_info = pd.read_sql("""
        SELECT customer_id, tier2_purchase_ratio, tier3_purchase_ratio
        FROM customer_features
    """, conn)
    cust_tier_map = cust_tier_info.set_index("customer_id")

    # Product-to-offer mapping
    product_to_offers = defaultdict(list)
    for _, row in active_offers.iterrows():
        product_to_offers[row["product_id"]].append(row["offer_id"])

    # Active offer set
    active_offer_set = set(active_offers["offer_id"].tolist())

    # Offer eligibility indexes
    offer_store_scope = {}
    offer_bt_scope = {}
    offer_sub_scope = {}
    offer_lt_scope = {}
    for _, row in active_offers.iterrows():
        oid = row["offer_id"]
        ss = row["store_scope"]
        offer_store_scope[oid] = set(ss.split(",")) if pd.notna(ss) and ss else None
        bts = row["business_type_scope"]
        offer_bt_scope[oid] = set(bts.split(",")) if pd.notna(bts) and bts else None
        subs = row["business_subtype_scope"]
        offer_sub_scope[oid] = set(subs.split(",")) if pd.notna(subs) and subs else None
        lts = row["loyalty_tier_scope"]
        offer_lt_scope[oid] = set(lts.split(",")) if pd.notna(lts) and lts else None

    # All categories for cross-sell
    all_categories = list(cat_to_offers.keys())

    # ---- Process customers in batches ----
    total_candidates = 0
    batch_size = 5000

    for batch_start in range(0, len(customers), batch_size):
        batch = customers.iloc[batch_start : batch_start + batch_size]
        insert_rows = []

        for _, cust in batch.iterrows():
            cid = cust["customer_id"]
            bt = cust["business_type"]
            sub = cust["business_subtype"]
            store = str(cust["home_store_id"])
            ltier = cust["loyalty_tier"]
            top_cats = cust_top_cats.get(cid, [])
            past_prods = cust_products.get(cid, set())
            purchased_cats = cust_purchased_cats.get(cid, set())

            candidates = {}  # offer_id -> strategy

            # --- Strategy 1: Category affinity ---
            limit = CANDIDATE_STRATEGY_LIMITS["category_affinity"]
            cat_candidates = []
            for cat in top_cats:
                cat_candidates.extend(cat_to_offers.get(cat, []))
            if len(cat_candidates) < limit:
                for cat in cat_to_offers:
                    if cat not in top_cats:
                        cat_candidates.extend(cat_to_offers[cat])
            for oid in cat_candidates[:limit]:
                if oid not in candidates and _is_eligible(
                    oid, bt, sub, store, ltier,
                    offer_store_scope, offer_bt_scope, offer_sub_scope, offer_lt_scope
                ):
                    candidates[oid] = "category_affinity"

            # --- Strategy 2: Business type popularity ---
            limit = CANDIDATE_STRATEGY_LIMITS["business_type_popular"]
            bt_offers = bt_pop_map.get(bt, [])
            count = 0
            for oid, _ in bt_offers:
                if oid in active_offer_set and oid not in candidates:
                    if _is_eligible(
                        oid, bt, sub, store, ltier,
                        offer_store_scope, offer_bt_scope, offer_sub_scope, offer_lt_scope
                    ):
                        candidates[oid] = "business_type_popular"
                        count += 1
                        if count >= limit:
                            break

            # --- Strategy 3: Repeat purchase ---
            limit = CANDIDATE_STRATEGY_LIMITS["repeat_purchase"]
            count = 0
            for prod_id in past_prods:
                if count >= limit:
                    break
                for oid in product_to_offers.get(prod_id, []):
                    if oid not in candidates and _is_eligible(
                        oid, bt, sub, store, ltier,
                        offer_store_scope, offer_bt_scope, offer_sub_scope, offer_lt_scope
                    ):
                        candidates[oid] = "repeat_purchase"
                        count += 1
                        if count >= limit:
                            break

            # --- Strategy 4: High margin ---
            for oid in high_margin_offers:
                if oid not in candidates and _is_eligible(
                    oid, bt, sub, store, ltier,
                    offer_store_scope, offer_bt_scope, offer_sub_scope, offer_lt_scope
                ):
                    candidates[oid] = "high_margin"

            # --- Strategy 5: Tier upgrade ---
            # Offer products where customer typically buys at tier1/tier2
            # and could save by buying more
            limit = CANDIDATE_STRATEGY_LIMITS["tier_upgrade"]
            if cid in cust_tier_map.index:
                tier_info = cust_tier_map.loc[cid]
                # Customers with low tier3 usage are good targets
                if tier_info.get("tier3_purchase_ratio", 0) < 0.3:
                    count = 0
                    for oid in active_offer_set:
                        if count >= limit:
                            break
                        if oid not in candidates and _is_eligible(
                            oid, bt, sub, store, ltier,
                            offer_store_scope, offer_bt_scope, offer_sub_scope, offer_lt_scope
                        ):
                            candidates[oid] = "tier_upgrade"
                            count += 1

            # --- Strategy 6: Cross-sell ---
            # Offer categories the customer hasn't purchased
            limit = CANDIDATE_STRATEGY_LIMITS["cross_sell"]
            count = 0
            for cat in all_categories:
                if count >= limit:
                    break
                if cat not in purchased_cats:
                    for oid in cat_to_offers.get(cat, []):
                        if count >= limit:
                            break
                        if oid not in candidates and _is_eligible(
                            oid, bt, sub, store, ltier,
                            offer_store_scope, offer_bt_scope, offer_sub_scope, offer_lt_scope
                        ):
                            candidates[oid] = "cross_sell"
                            count += 1

            # --- Strategy 7: Own brand switch ---
            limit = CANDIDATE_STRATEGY_LIMITS["own_brand_switch"]
            count = 0
            for oid in own_brand_offers:
                if count >= limit:
                    break
                if oid not in candidates and _is_eligible(
                    oid, bt, sub, store, ltier,
                    offer_store_scope, offer_bt_scope, offer_sub_scope, offer_lt_scope
                ):
                    candidates[oid] = "own_brand_switch"
                    count += 1

            # Cap at CANDIDATE_POOL_SIZE
            for oid, strategy in list(candidates.items())[:CANDIDATE_POOL_SIZE]:
                insert_rows.append((cid, oid, strategy, run_date))

            total_candidates += min(len(candidates), CANDIDATE_POOL_SIZE)

        # Batch insert
        conn.executemany(
            "INSERT OR IGNORE INTO candidate_pool (customer_id, offer_id, strategy, run_date) VALUES (?,?,?,?)",
            insert_rows,
        )
        conn.commit()

    logger.info(
        f"  Candidate pool: {total_candidates:,} total "
        f"(avg {total_candidates / max(len(customers), 1):.0f} per customer)"
    )


def _is_eligible(offer_id, business_type, business_subtype, store_id, loyalty_tier,
                 store_scope_map, bt_scope_map, sub_scope_map, lt_scope_map):
    """Check if an offer is eligible for a customer based on scope rules."""
    # Business type scope
    bt_scope = bt_scope_map.get(offer_id)
    if bt_scope is not None and business_type not in bt_scope:
        return False

    # Business subtype scope
    sub_scope = sub_scope_map.get(offer_id)
    if sub_scope is not None and business_subtype not in sub_scope:
        return False

    # Loyalty tier scope
    lt_scope = lt_scope_map.get(offer_id)
    if lt_scope is not None and loyalty_tier not in lt_scope:
        return False

    # Store scope
    st_scope = store_scope_map.get(offer_id)
    if st_scope is not None and store_id not in st_scope:
        return False

    return True
