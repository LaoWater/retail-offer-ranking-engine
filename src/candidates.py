"""
Candidate generation for Metro Personalized Offers Recommender.

Retrieves ~200 eligible offers per customer using 4 heuristic strategies:
  1. Category affinity (80 candidates)
  2. Segment popularity (60 candidates)
  3. Repeat purchase (40 candidates)
  4. High margin (20 candidates)

This is stage 1 of the two-stage recommender (retrieval -> ranking).
"""

import logging
from collections import defaultdict

import pandas as pd
import numpy as np

from src.config import CANDIDATE_POOL_SIZE, CANDIDATE_STRATEGY_LIMITS

logger = logging.getLogger(__name__)


def generate_candidate_pool(conn, run_date):
    """
    Generate candidate offers for all customers and write to candidate_pool table.

    Processes customers in batches for memory efficiency.
    """
    logger.info("Generating candidate pool...")

    # Clear existing candidates for this date
    conn.execute("DELETE FROM candidate_pool WHERE run_date = ?", (run_date,))
    conn.commit()

    # ---- Load reference data ----

    # Active offers on run_date
    active_offers = pd.read_sql("""
        SELECT o.offer_id, o.product_id, o.store_scope, o.segment_scope,
               o.discount_value, o.discount_type,
               p.category, p.margin, p.base_price
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

    # Offer margin for high-margin strategy
    active_offers["effective_margin"] = (
        active_offers["base_price"] * active_offers["margin"]
    )
    high_margin_offers = (
        active_offers.nlargest(CANDIDATE_STRATEGY_LIMITS["high_margin"], "effective_margin")["offer_id"]
        .tolist()
    )

    # Segment popularity: count impressions per offer per segment
    seg_popularity = pd.read_sql("""
        SELECT c.segment, i.offer_id, COUNT(*) AS imp_count
        FROM impressions i
        JOIN customers c ON i.customer_id = c.customer_id
        GROUP BY c.segment, i.offer_id
    """, conn)
    seg_pop_map = defaultdict(list)
    for _, row in seg_popularity.iterrows():
        seg_pop_map[row["segment"]].append((row["offer_id"], row["imp_count"]))
    # Sort by popularity descending
    for seg in seg_pop_map:
        seg_pop_map[seg].sort(key=lambda x: -x[1])

    # Customer data
    customers = pd.read_sql("""
        SELECT customer_id, segment, home_store_id
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

    # Customer purchased products (last 90 days for repeat-purchase strategy)
    cust_products_raw = pd.read_sql("""
        SELECT DISTINCT o.customer_id, oi.product_id
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE DATE(o.order_timestamp) >= DATE(:rd, '-90 days')
    """, conn, params={"rd": run_date})
    cust_products = defaultdict(set)
    for _, row in cust_products_raw.iterrows():
        cust_products[row["customer_id"]].add(row["product_id"])

    # Product-to-offer mapping
    product_to_offers = defaultdict(list)
    for _, row in active_offers.iterrows():
        product_to_offers[row["product_id"]].append(row["offer_id"])

    # Active offer set for fast lookup
    active_offer_set = set(active_offers["offer_id"].tolist())

    # Offer eligibility index
    offer_store_scope = {}
    offer_segment_scope = {}
    for _, row in active_offers.iterrows():
        oid = row["offer_id"]
        ss = row["store_scope"]
        offer_store_scope[oid] = set(ss.split(",")) if pd.notna(ss) and ss else None
        segs = row["segment_scope"]
        offer_segment_scope[oid] = set(segs.split(",")) if pd.notna(segs) and segs else None

    # ---- Process customers in batches ----
    total_candidates = 0
    batch_size = 5000

    for batch_start in range(0, len(customers), batch_size):
        batch = customers.iloc[batch_start : batch_start + batch_size]
        insert_rows = []

        for _, cust in batch.iterrows():
            cid = cust["customer_id"]
            seg = cust["segment"]
            store = str(cust["home_store_id"])
            top_cats = cust_top_cats.get(cid, [])
            past_prods = cust_products.get(cid, set())

            candidates = {}  # offer_id -> strategy

            # --- Strategy 1: Category affinity ---
            limit = CANDIDATE_STRATEGY_LIMITS["category_affinity"]
            cat_candidates = []
            for cat in top_cats:
                cat_candidates.extend(cat_to_offers.get(cat, []))
            # Also include offers from related categories
            if len(cat_candidates) < limit:
                for cat in cat_to_offers:
                    if cat not in top_cats:
                        cat_candidates.extend(cat_to_offers[cat])
            for oid in cat_candidates[:limit]:
                if oid not in candidates and _is_eligible(oid, seg, store, offer_store_scope, offer_segment_scope):
                    candidates[oid] = "category_affinity"

            # --- Strategy 2: Segment popularity ---
            limit = CANDIDATE_STRATEGY_LIMITS["segment_popular"]
            seg_offers = seg_pop_map.get(seg, [])
            count = 0
            for oid, _ in seg_offers:
                if oid in active_offer_set and oid not in candidates:
                    if _is_eligible(oid, seg, store, offer_store_scope, offer_segment_scope):
                        candidates[oid] = "segment_popular"
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
                    if oid not in candidates and _is_eligible(oid, seg, store, offer_store_scope, offer_segment_scope):
                        candidates[oid] = "repeat_purchase"
                        count += 1
                        if count >= limit:
                            break

            # --- Strategy 4: High margin ---
            for oid in high_margin_offers:
                if oid not in candidates and _is_eligible(oid, seg, store, offer_store_scope, offer_segment_scope):
                    candidates[oid] = "high_margin"

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


def _is_eligible(offer_id, segment, store_id, store_scope_map, segment_scope_map):
    """Check if an offer is eligible for a customer based on scope rules."""
    # Segment scope
    seg_scope = segment_scope_map.get(offer_id)
    if seg_scope is not None and segment not in seg_scope:
        return False

    # Store scope
    st_scope = store_scope_map.get(offer_id)
    if st_scope is not None and store_id not in st_scope:
        return False

    return True
