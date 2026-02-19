"""
Daily behavior simulator for Metro Romania Recommender.

Generates fresh customer activity (orders, impressions, redemptions) for a
given run_date by reusing MetroDataGenerator helper methods. This creates
the feedback loop that makes the system feel like a living demo:

- Day-of-week signal: Monday → HoReCa dominates (1.4x multiplier)
- Seasonal signal: Christmas → 2.5x orders, meat/deli top categories
- Drift feedback: recency_days/frequency genuinely shift after several runs
- Meaningful evaluation: NDCG/MRR score against real forward redemptions

Usage (called from daily_run.py as step 0):
    from src.simulate_day_behavior import simulate_day
    summary = simulate_day(conn, "2026-02-19")
"""

import logging
from datetime import datetime, timedelta, date
from typing import Optional

import numpy as np

from src.config import (
    SEED, BUSINESS_TYPE_DIST, BUSINESS_SUBTYPE_DIST, BUSINESS_PROFILES,
    BUSINESS_CATEGORY_AFFINITY, WEEKLY_PATTERNS, SEASONAL_EVENTS,
    CATEGORY_NAMES, CATEGORY_WEIGHTS, PURCHASE_MODE_DIST,
    INDIVIDUAL_PURCHASE_PROFILE, CHANNEL_DIST, TARGET_REDEMPTION_RATE,
)
from src.generate_data import MetroDataGenerator

logger = logging.getLogger(__name__)


def simulate_day(conn, run_date: str) -> dict:
    """
    Generate fresh customer activity for run_date and insert it into the DB.

    Returns a summary dict with:
        orders_generated, impressions_shown, redemptions_made,
        redemption_rate, orders_by_segment, avg_basket_size, top_category
    """
    run_date_obj = datetime.strptime(run_date, "%Y-%m-%d").date()
    dow = run_date_obj.weekday()          # 0=Mon ... 6=Sun
    doy = run_date_obj.timetuple().tm_yday

    # Day-specific seed so each simulated day produces different numbers
    # while still being reproducible (same date → same result)
    day_seed = SEED ^ int(run_date.replace("-", ""))
    generator = MetroDataGenerator(seed=day_seed)

    seasonal_mult = generator._get_seasonal_multiplier(doy)
    logger.info(f"  Day-of-week: {dow} (0=Mon), seasonal_mult: {seasonal_mult:.2f}")

    # ------------------------------------------------------------------ #
    # 1.  Load customers (vectorized)
    # ------------------------------------------------------------------ #
    rows = conn.execute(
        "SELECT customer_id, business_type, business_subtype, "
        "home_store_id, email_consent, sms_consent, app_registered "
        "FROM customers"
    ).fetchall()

    if not rows:
        logger.warning("No customers found — skipping behavior simulation")
        return {
            "orders_generated": 0, "impressions_shown": 0, "redemptions_made": 0,
            "redemption_rate": 0.0, "orders_by_segment": {}, "avg_basket_size": 0.0,
            "top_category": None,
        }

    n_customers = len(rows)
    customer_ids   = np.array([r[0] for r in rows], dtype=np.int64)
    business_types = [r[1] for r in rows]
    subtypes       = [r[2] for r in rows]
    store_ids      = np.array([r[3] for r in rows], dtype=np.int32)
    email_consent  = np.array([r[4] for r in rows], dtype=bool)
    sms_consent    = np.array([r[5] for r in rows], dtype=bool)
    app_registered = np.array([r[6] for r in rows], dtype=bool)

    # ------------------------------------------------------------------ #
    # 2.  Compute per-customer order probability (vectorized)
    # ------------------------------------------------------------------ #
    rng = generator.rng

    freq_arr = np.array(
        [BUSINESS_PROFILES[sub].get("purchase_freq_weekly", 1.0) for sub in subtypes],
        dtype=float,
    )
    weekly_mult_arr = np.array(
        [WEEKLY_PATTERNS.get(bt, {}).get(dow, 1.0) for bt in business_types],
        dtype=float,
    )

    p_order = np.minimum(1.0, freq_arr / 7.0 * weekly_mult_arr * seasonal_mult * 0.6)
    p_order *= rng.uniform(0.85, 1.15, size=n_customers)
    p_order = np.clip(p_order, 0.0, 1.0)

    ordering_mask = rng.random(n_customers) < p_order
    ordering_indices = np.where(ordering_mask)[0]
    logger.info(f"  {len(ordering_indices):,} customers will order today")

    # ------------------------------------------------------------------ #
    # 3.  Get the next available order_id and order_item_id
    # ------------------------------------------------------------------ #
    max_order_id = conn.execute("SELECT COALESCE(MAX(order_id), 0) FROM orders").fetchone()[0]
    max_item_id  = conn.execute("SELECT COALESCE(MAX(order_item_id), 0) FROM order_items").fetchone()[0]
    order_id     = int(max_order_id)
    order_item_id = int(max_item_id)

    # ------------------------------------------------------------------ #
    # 4.  Load product catalogue (needed for item generation)
    # ------------------------------------------------------------------ #
    prod_rows = conn.execute(
        "SELECT product_id, category, tier1_price, tier2_price, tier2_min_qty, "
        "tier3_price, tier3_min_qty FROM products"
    ).fetchall()

    from collections import defaultdict
    cat_to_products = defaultdict(list)
    product_info = {}
    for pr in prod_rows:
        pid, cat = pr[0], pr[1]
        cat_to_products[cat].append(pid)
        product_info[pid] = {
            "category": cat,
            "tier1_price": pr[2],
            "tier2_price": pr[3],
            "tier2_min_qty": pr[4],
            "tier3_price": pr[5],
            "tier3_min_qty": pr[6],
        }

    cat_weights_arr = np.array(CATEGORY_WEIGHTS, dtype=float)
    cat_weights_arr /= cat_weights_arr.sum()

    # ------------------------------------------------------------------ #
    # 5.  Generate orders + items
    # ------------------------------------------------------------------ #
    order_rows_buf = []
    item_rows_buf  = []
    orders_today   = {}        # customer_id → order_id (last order of the day)
    category_counts = defaultdict(int)
    segment_counts  = defaultdict(int)
    basket_sizes    = []

    for idx in ordering_indices:
        cid  = int(customer_ids[idx])
        bt   = business_types[idx]
        sub  = subtypes[idx]
        sid  = int(store_ids[idx])
        profile = BUSINESS_PROFILES[sub]

        purchase_mode = rng.choice(
            list(PURCHASE_MODE_DIST.keys()),
            p=list(PURCHASE_MODE_DIST.values()),
        )
        is_individual = purchase_mode == "individual"

        basket_mean = profile["basket_size_mean"]
        basket_std  = profile["basket_size_std"]
        if is_individual:
            basket_mean = max(3, int(basket_mean * INDIVIDUAL_PURCHASE_PROFILE["basket_size_multiplier"]))
            basket_std  = max(2, int(basket_std * 0.5))
        n_items = max(1, int(rng.normal(basket_mean, basket_std)))

        # Category affinity for this customer
        sub_aff = BUSINESS_CATEGORY_AFFINITY.get(sub, {})
        cat_aff = cat_weights_arr.copy()
        for i, cname in enumerate(CATEGORY_NAMES):
            cat_aff[i] *= sub_aff.get(cname, 1.0)
        cat_aff = np.maximum(cat_aff, 0.001)
        cat_aff /= cat_aff.sum()

        chosen_cats = rng.choice(CATEGORY_NAMES, size=n_items, p=cat_aff)

        order_id += 1
        order_total           = 0.0
        order_total_before    = 0.0
        order_total_qty       = 0
        items_in_order        = 0

        for chosen_cat in chosen_cats:
            prods = cat_to_products.get(chosen_cat)
            if not prods:
                continue

            pid   = int(rng.choice(prods))
            pinfo = product_info[pid]

            if is_individual:
                lo, hi   = INDIVIDUAL_PURCHASE_PROFILE["quantity_range"]
                quantity = int(rng.integers(lo, hi + 1))
            else:
                quantity = generator._get_wholesale_quantity(bt, sub, chosen_cat)

            # Tier
            tier_applied = 1
            unit_price   = pinfo["tier1_price"]
            if is_individual:
                r = rng.random()
                if r < INDIVIDUAL_PURCHASE_PROFILE["tier3_probability"] and quantity >= pinfo["tier3_min_qty"]:
                    tier_applied = 3; unit_price = pinfo["tier3_price"]
                elif r < INDIVIDUAL_PURCHASE_PROFILE["tier2_probability"] and quantity >= pinfo["tier2_min_qty"]:
                    tier_applied = 2; unit_price = pinfo["tier2_price"]
            else:
                if quantity >= pinfo["tier3_min_qty"]:
                    tier_applied = 3; unit_price = pinfo["tier3_price"]
                elif quantity >= pinfo["tier2_min_qty"]:
                    tier_applied = 2; unit_price = pinfo["tier2_price"]

            unit_price    = round(unit_price * (1 + rng.normal(0, 0.02)), 2)
            unit_price    = max(0.50, unit_price)
            tier_savings  = max(0.0, round(pinfo["tier1_price"] - unit_price, 2))

            is_promo     = int(rng.random() < profile.get("promo_affinity", 0.5) * 0.3)
            discount_amt = 0.0
            if is_promo:
                disc_pct     = rng.uniform(0.05, 0.35)
                discount_amt = round(unit_price * disc_pct, 2)

            order_item_id += 1
            item_rows_buf.append((
                order_item_id, order_id, pid, quantity,
                unit_price, tier_applied, tier_savings,
                is_promo, discount_amt, None,
            ))

            order_total        += (unit_price - discount_amt) * quantity
            order_total_before += pinfo["tier1_price"] * quantity
            order_total_qty    += quantity
            items_in_order     += 1
            category_counts[chosen_cat] += 1

        if items_in_order == 0:
            order_id -= 1
            continue

        hour   = int(rng.choice([6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17]))
        minute = int(rng.integers(0, 60))
        ts     = datetime.combine(run_date_obj, datetime.min.time()).replace(
            hour=hour, minute=minute
        )

        payment = rng.choice(["card", "cash", "transfer"], p=[0.50, 0.30, 0.20])

        order_rows_buf.append((
            order_id, cid, sid, ts.isoformat(),
            round(order_total, 2), round(order_total_before, 2),
            order_total_qty, items_in_order, purchase_mode, payment,
        ))

        orders_today[cid] = order_id
        segment_counts[bt] += 1
        basket_sizes.append(items_in_order)

        # Flush every 5K orders
        if len(order_rows_buf) >= 5000:
            generator._flush_orders(conn, order_rows_buf, item_rows_buf)
            order_rows_buf.clear()
            item_rows_buf.clear()

    if order_rows_buf:
        generator._flush_orders(conn, order_rows_buf, item_rows_buf)

    orders_generated = len(orders_today)
    avg_basket_size  = float(np.mean(basket_sizes)) if basket_sizes else 0.0
    top_category     = max(category_counts, key=category_counts.get) if category_counts else None
    logger.info(f"  Generated {orders_generated:,} orders, top category: {top_category}")

    # ------------------------------------------------------------------ #
    # 6.  Generate impressions from previous day's recommendations
    # ------------------------------------------------------------------ #
    prev_run_row = conn.execute("""
        SELECT MAX(run_date) FROM recommendations
        WHERE run_date < ?
    """, (run_date,)).fetchone()
    prev_run_date: Optional[str] = prev_run_row[0] if prev_run_row else None

    impression_rows_buf = []
    redemption_rows_buf = []

    max_imp_id    = conn.execute("SELECT COALESCE(MAX(impression_id), 0) FROM impressions").fetchone()[0]
    max_redeem_id = conn.execute("SELECT COALESCE(MAX(redemption_id), 0) FROM redemptions").fetchone()[0]
    impression_id  = int(max_imp_id)
    redemption_id  = int(max_redeem_id)

    channel_names   = list(CHANNEL_DIST.keys())
    channel_weights = list(CHANNEL_DIST.values())

    if prev_run_date:
        rec_rows = conn.execute("""
            SELECT r.customer_id, r.offer_id
            FROM recommendations r
            WHERE r.run_date = ?
        """, (prev_run_date,)).fetchall()

        # Load offer info for redemption probability
        offer_info_map = {}
        offer_rows = conn.execute("""
            SELECT o.offer_id, o.offer_type, o.discount_value, p.category,
                   p.tier1_price, p.product_id, o.business_type_scope, o.store_scope,
                   o.campaign_type
            FROM offers o
            JOIN products p ON o.product_id = p.product_id
        """).fetchall()
        for or_ in offer_rows:
            offer_info_map[or_[0]] = {
                "offer_type":          or_[1],
                "discount_value":      or_[2],
                "category":            or_[3],
                "tier1_price":         or_[4],
                "product_id":          or_[5],
                "business_type_scope": or_[6],
                "store_scope":         or_[7],
                "campaign_type":       or_[8],
            }

        # Load customer top categories from features (if available)
        cust_top_cats: dict = {}
        feat_rows = conn.execute(
            "SELECT customer_id, top_3_categories FROM customer_features"
        ).fetchall()
        for fr in feat_rows:
            raw = fr[1]
            if raw:
                try:
                    import json
                    cats = json.loads(raw)
                except Exception:
                    cats = [c.strip() for c in str(raw).split(",")]
                cust_top_cats[fr[0]] = set(cats)

        # Load customer purchased products (for prior purchase boost)
        cust_products: dict = {}
        prod_hist_rows = conn.execute("""
            SELECT DISTINCT o.customer_id, oi.product_id
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
        """).fetchall()
        for phr in prod_hist_rows:
            cid_, pid_ = phr[0], phr[1]
            if cid_ not in cust_products:
                cust_products[cid_] = set()
            cust_products[cid_].add(pid_)

        # Build customer channel eligibility lookup
        channel_eligible: dict = {}
        for i, cid in enumerate(customer_ids):
            eligible = []
            if email_consent[i]:
                eligible.append("email")
            if sms_consent[i]:
                eligible.append("sms")
            if app_registered[i]:
                eligible.append("app")
            if not eligible:
                eligible.append("email")  # fallback
            channel_eligible[int(cid)] = eligible

        # Build a quick lookup: customer_id → (business_type, business_subtype)
        cust_meta: dict = {}
        for i, cid in enumerate(customer_ids):
            cust_meta[int(cid)] = (business_types[i], subtypes[i])

        for rec_row in rec_rows:
            cid_, oid_ = int(rec_row[0]), int(rec_row[1])
            if oid_ not in offer_info_map:
                continue

            eligible = channel_eligible.get(cid_, ["email"])
            # Pick channel from eligible intersection with global dist
            weighted = [(ch, w) for ch, w in zip(channel_names, channel_weights) if ch in eligible]
            if not weighted:
                weighted = [(ch, w) for ch, w in zip(channel_names, channel_weights)]
            chs, wts = zip(*weighted)
            wts_arr = np.array(wts, dtype=float)
            wts_arr /= wts_arr.sum()
            channel = rng.choice(list(chs), p=wts_arr)

            # Random hour between 08:00-20:00
            hour_   = int(rng.integers(8, 21))
            minute_ = int(rng.integers(0, 60))
            imp_ts  = datetime.combine(run_date_obj, datetime.min.time()).replace(
                hour=hour_, minute=minute_
            )

            impression_id += 1
            ctype_ = offer_info_map[oid_].get("campaign_type")
            impression_rows_buf.append((
                impression_id, cid_, oid_, imp_ts.isoformat(), channel, ctype_,
            ))

            # Redemption probability
            bt_, sub_ = cust_meta.get(cid_, ("horeca", "restaurant"))
            top_cats  = cust_top_cats.get(cid_, set())
            prods     = cust_products.get(cid_, set())
            promo_aff = BUSINESS_PROFILES.get(sub_, {}).get("promo_affinity", 0.5)

            p_redeem = generator._compute_redemption_prob(
                offer_info_map[oid_], promo_aff, top_cats, prods, bt_, sub_
            )

            if rng.random() < p_redeem and cid_ in orders_today:
                redeem_delay = int(rng.integers(0, 3))
                redeem_ts    = imp_ts + timedelta(days=redeem_delay)
                disc_applied = generator._compute_discount_amount(offer_info_map[oid_])

                redemption_id += 1
                redemption_rows_buf.append((
                    redemption_id, cid_, oid_, orders_today[cid_],
                    redeem_ts.isoformat(), channel, disc_applied,
                ))

            # Batch flush impressions
            if len(impression_rows_buf) >= 50000:
                generator._flush_impressions(conn, impression_rows_buf, redemption_rows_buf)
                impression_rows_buf.clear()
                redemption_rows_buf.clear()

    if impression_rows_buf:
        generator._flush_impressions(conn, impression_rows_buf, redemption_rows_buf)

    impressions_shown  = impression_id  - int(max_imp_id)
    redemptions_made   = redemption_id  - int(max_redeem_id)
    redemption_rate    = round(redemptions_made / max(1, impressions_shown), 4)

    logger.info(
        f"  Impressions: {impressions_shown:,}, Redemptions: {redemptions_made:,} "
        f"({redemption_rate * 100:.1f}%)"
    )

    return {
        "orders_generated":  orders_generated,
        "impressions_shown":  impressions_shown,
        "redemptions_made":   redemptions_made,
        "redemption_rate":    redemption_rate,
        "orders_by_segment":  dict(segment_counts),
        "avg_basket_size":    round(avg_basket_size, 1),
        "top_category":       top_category,
    }
