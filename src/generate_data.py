"""
Synthetic data generator for Metro Personalized Offers Recommender.

Generates realistic supermarket data with correlated customer segments,
temporal purchase patterns, and promotional behavior.

Usage:
    python -m src.generate_data
    python -m src.generate_data --customers 1000 --products 500 --offers 50
"""

import argparse
import logging
import time
import json
import math
from datetime import datetime, timedelta, date

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.config import (
    SEED, N_CUSTOMERS, N_PRODUCTS, N_OFFERS, N_STORES, HISTORY_DAYS,
    TARGET_ORDER_ITEMS, TARGET_IMPRESSIONS, TARGET_REDEMPTION_RATE,
    SEGMENT_DIST, LOYALTY_TIERS, CATEGORY_NAMES, CATEGORY_WEIGHTS,
    SUBCATEGORIES, CATEGORY_PRICE_RANGE, CATEGORY_MARGIN_RANGE,
    CATEGORY_SHELF_LIFE, SEGMENT_PROFILES, SEGMENT_CATEGORY_AFFINITY,
    BRANDS_PER_CATEGORY, SEASONAL_EVENTS, DB_PATH, DATA_DIR, MODELS_DIR,
    LOGS_DIR,
)
from src.db import get_connection, init_db

logger = logging.getLogger(__name__)


class MetroDataGenerator:
    """Generates realistic synthetic data for the Metro recommendation pipeline."""

    def __init__(
        self,
        seed=SEED,
        n_customers=N_CUSTOMERS,
        n_products=N_PRODUCTS,
        n_offers=N_OFFERS,
        n_stores=N_STORES,
        history_days=HISTORY_DAYS,
        target_order_items=TARGET_ORDER_ITEMS,
        target_impressions=TARGET_IMPRESSIONS,
    ):
        self.rng = np.random.default_rng(seed)
        self.n_customers = n_customers
        self.n_products = n_products
        self.n_offers = n_offers
        self.n_stores = n_stores
        self.history_days = history_days
        self.target_order_items = target_order_items
        self.target_impressions = target_impressions

        self.end_date = date(2026, 2, 11)
        self.start_date = self.end_date - timedelta(days=history_days)

        # Derived data stored for cross-referencing during generation
        self._customers_df = None
        self._products_df = None
        self._orders_df = None
        self._offers_df = None

    # ------------------------------------------------------------------
    # Master orchestration
    # ------------------------------------------------------------------

    def generate_all(self, db_path=None):
        """Generate all tables and write to the database."""
        t_total = time.time()
        path = db_path or DB_PATH

        for d in (DATA_DIR, MODELS_DIR, LOGS_DIR):
            d.mkdir(parents=True, exist_ok=True)

        conn = get_connection(path)
        init_db(conn)

        # Turn off foreign keys during bulk load for speed
        conn.execute("PRAGMA foreign_keys=OFF")

        logger.info("Generating customers...")
        self._generate_customers(conn)

        logger.info("Generating products...")
        self._generate_products(conn)

        logger.info("Generating orders and order items...")
        self._generate_orders_and_items(conn)

        logger.info("Generating offers...")
        self._generate_offers(conn)

        logger.info("Generating impressions and redemptions...")
        self._generate_impressions_and_redemptions(conn)

        conn.execute("PRAGMA foreign_keys=ON")
        conn.commit()

        # Print summary
        self._print_summary(conn)
        elapsed = time.time() - t_total
        logger.info(f"Data generation completed in {elapsed:.1f}s")

        conn.close()

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    def _generate_customers(self, conn):
        segments = list(SEGMENT_DIST.keys())
        seg_probs = list(SEGMENT_DIST.values())

        seg_arr = self.rng.choice(segments, size=self.n_customers, p=seg_probs)

        # Loyalty tier correlated with segment
        loyalty = []
        for seg in seg_arr:
            tiers = list(LOYALTY_TIERS[seg].keys())
            probs = list(LOYALTY_TIERS[seg].values())
            loyalty.append(self.rng.choice(tiers, p=probs))

        # Home store - some stores are clustered by type
        store_ids = self.rng.integers(1, self.n_stores + 1, size=self.n_customers)

        # Join dates - skewed toward recent (exponential)
        days_ago = self.rng.exponential(scale=365, size=self.n_customers).astype(int)
        days_ago = np.clip(days_ago, 30, 1095)  # 1 month to 3 years
        join_dates = [
            (self.end_date - timedelta(days=int(d))).isoformat() for d in days_ago
        ]

        # Email consent correlated with segment
        email_consent = []
        for seg in seg_arr:
            rate = SEGMENT_PROFILES[seg]["email_consent_rate"]
            email_consent.append(int(self.rng.random() < rate))

        df = pd.DataFrame({
            "customer_id": range(1, self.n_customers + 1),
            "segment": seg_arr,
            "home_store_id": store_ids,
            "join_date": join_dates,
            "loyalty_tier": loyalty,
            "email_consent": email_consent,
        })

        df.to_sql("customers", conn, if_exists="append", index=False)
        conn.commit()
        self._customers_df = df
        logger.info(f"  Created {len(df):,} customers")

    # ------------------------------------------------------------------
    # Products
    # ------------------------------------------------------------------

    def _generate_products(self, conn):
        cat_weights = np.array(CATEGORY_WEIGHTS, dtype=float)
        cat_weights /= cat_weights.sum()

        categories = self.rng.choice(
            CATEGORY_NAMES, size=self.n_products, p=cat_weights
        )

        rows = []
        for pid in range(1, self.n_products + 1):
            cat = categories[pid - 1]
            subcats = SUBCATEGORIES.get(cat, ["general"])
            subcat = self.rng.choice(subcats)

            # Brand: mix of store brand and named brands
            brand_num = self.rng.integers(1, BRANDS_PER_CATEGORY + 1)
            is_store_brand = brand_num <= 2
            brand = f"store_brand_{brand_num}" if is_store_brand else f"{cat}_brand_{brand_num}"

            # Price: log-normal within category range
            pmin, pmax = CATEGORY_PRICE_RANGE[cat]
            log_mean = (math.log(pmin) + math.log(pmax)) / 2
            log_std = (math.log(pmax) - math.log(pmin)) / 4
            price = float(np.exp(self.rng.normal(log_mean, log_std)))
            price = round(max(pmin, min(pmax * 1.5, price)), 2)

            # Store brands are cheaper
            if is_store_brand:
                price = round(price * 0.7, 2)

            # Margin
            mmin, mmax = CATEGORY_MARGIN_RANGE[cat]
            margin = round(float(self.rng.uniform(mmin, mmax)), 3)
            if is_store_brand:
                margin = round(margin * 1.4, 3)  # Higher margin on store brands

            # Shelf life
            sl_min, sl_max = CATEGORY_SHELF_LIFE[cat]
            shelf_life = int(self.rng.integers(sl_min, sl_max + 1))

            name = f"{brand}_{subcat}_{pid}"

            rows.append({
                "product_id": pid,
                "name": name,
                "category": cat,
                "subcategory": subcat,
                "brand": brand,
                "base_price": price,
                "margin": margin,
                "shelf_life_days": shelf_life,
            })

        df = pd.DataFrame(rows)
        df.to_sql("products", conn, if_exists="append", index=False)
        conn.commit()
        self._products_df = df
        logger.info(f"  Created {len(df):,} products across {len(CATEGORY_NAMES)} categories")

    # ------------------------------------------------------------------
    # Orders & Order Items
    # ------------------------------------------------------------------

    def _generate_orders_and_items(self, conn):
        customers = self._customers_df
        products = self._products_df

        # Pre-compute product lookup by category
        cat_to_products = {}
        for cat in CATEGORY_NAMES:
            mask = products["category"] == cat
            cat_to_products[cat] = products.loc[mask, "product_id"].values

        # All product ids and prices for fast lookup
        product_prices = products.set_index("product_id")["base_price"].to_dict()

        total_items = 0
        order_id = 0
        order_item_id = 0

        order_rows = []
        item_rows = []

        # Compute per-customer category affinity vectors
        # (segment base + per-customer noise)
        n_cats = len(CATEGORY_NAMES)

        for batch_start in tqdm(
            range(0, self.n_customers, 5000),
            desc="Generating orders",
            unit="batch",
        ):
            batch_end = min(batch_start + 5000, self.n_customers)
            batch = customers.iloc[batch_start:batch_end]

            for _, cust in batch.iterrows():
                cid = cust["customer_id"]
                seg = cust["segment"]
                store_id = cust["home_store_id"]
                profile = SEGMENT_PROFILES[seg]

                # Customer-specific purchase frequency with noise
                freq = profile["purchase_freq_weekly"] * (
                    1 + self.rng.normal(0, 0.25)
                )
                freq = max(0.1, freq)

                # Customer-specific category affinity
                cat_affinity = np.array(CATEGORY_WEIGHTS, dtype=float)
                seg_aff = SEGMENT_CATEGORY_AFFINITY.get(seg, {})
                for i, cat_name in enumerate(CATEGORY_NAMES):
                    cat_affinity[i] *= seg_aff.get(cat_name, 1.0)
                # Add per-customer noise
                cat_affinity *= (1 + self.rng.normal(0, 0.2, size=n_cats))
                cat_affinity = np.maximum(cat_affinity, 0.001)
                cat_affinity /= cat_affinity.sum()

                # Customer promo affinity (from profile + noise)
                cust_promo_aff = max(
                    0.0,
                    min(1.0, profile["promo_affinity"] + self.rng.normal(0, 0.1)),
                )

                # Generate order timestamps over the history window
                avg_orders = freq * (self.history_days / 7.0)
                n_orders = max(1, int(self.rng.poisson(avg_orders)))

                # Random days within the window
                order_days = self.rng.integers(0, self.history_days, size=n_orders)
                order_days.sort()

                for day_offset in order_days:
                    order_date = self.start_date + timedelta(days=int(day_offset))
                    dow = order_date.weekday()  # 0=Mon, 6=Sun
                    dom = order_date.day
                    doy = order_date.timetuple().tm_yday

                    # Time-varying intensity filter
                    # Weekly: peak on Saturday (5), trough on Tuesday (1)
                    weekly_mult = 1.0 + 0.3 * math.cos(
                        2 * math.pi * (dow - 5) / 7
                    )
                    # Monthly payday: spike days 25-31 and 1-3
                    monthly_mult = 1.2 if (dom >= 25 or dom <= 3) else 1.0
                    # Seasonal
                    seasonal_mult = self._get_seasonal_multiplier(doy)
                    # Acceptance probability
                    accept_prob = min(1.0, weekly_mult * monthly_mult * seasonal_mult * 0.6)
                    if self.rng.random() > accept_prob:
                        continue

                    order_id += 1

                    # Basket size
                    basket_mean = profile["basket_size_mean"]
                    basket_std = profile["basket_size_std"]
                    n_items = max(
                        1,
                        int(self.rng.normal(basket_mean, basket_std)),
                    )

                    # Select products for this basket
                    chosen_cats = self.rng.choice(
                        CATEGORY_NAMES, size=n_items, p=cat_affinity
                    )

                    order_total = 0.0
                    for chosen_cat in chosen_cats:
                        prods_in_cat = cat_to_products.get(chosen_cat)
                        if prods_in_cat is None or len(prods_in_cat) == 0:
                            continue

                        prod_id = int(self.rng.choice(prods_in_cat))
                        quantity = int(
                            self.rng.choice([1, 1, 1, 2, 2, 3])
                            if seg != "horeca"
                            else self.rng.choice([5, 10, 12, 20, 24])
                        )
                        unit_price = round(
                            product_prices[prod_id]
                            * (1 + self.rng.normal(0, 0.03)),
                            2,
                        )
                        unit_price = max(0.10, unit_price)

                        # Promo behavior
                        is_promo = int(self.rng.random() < cust_promo_aff * 0.3)
                        discount_amt = 0.0
                        if is_promo:
                            disc_pct = self.rng.uniform(0.05, 0.35)
                            discount_amt = round(unit_price * disc_pct, 2)

                        order_item_id += 1
                        item_rows.append((
                            order_item_id,
                            order_id,
                            prod_id,
                            quantity,
                            unit_price,
                            is_promo,
                            discount_amt,
                        ))
                        order_total += (unit_price - discount_amt) * quantity

                    if not item_rows or item_rows[-1][1] != order_id:
                        order_id -= 1
                        continue

                    # Count items in this order
                    items_in_order = 0
                    for row in reversed(item_rows):
                        if row[1] == order_id:
                            items_in_order += 1
                        else:
                            break

                    hour = int(self.rng.choice([8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19]))
                    minute = int(self.rng.integers(0, 60))
                    ts = datetime.combine(
                        order_date, datetime.min.time()
                    ).replace(hour=hour, minute=minute)

                    order_rows.append((
                        order_id,
                        cid,
                        store_id,
                        ts.isoformat(),
                        round(order_total, 2),
                        items_in_order,
                    ))

                    total_items += items_in_order

            # Batch insert periodically
            if len(order_rows) > 50000:
                self._flush_orders(conn, order_rows, item_rows)
                order_rows.clear()
                item_rows.clear()

            # Check if we've hit the target
            if total_items >= self.target_order_items:
                break

        # Final flush
        if order_rows:
            self._flush_orders(conn, order_rows, item_rows)

        logger.info(f"  Created {order_id:,} orders with {total_items:,} items")

        # Store for later use
        self._total_orders = order_id

    def _flush_orders(self, conn, order_rows, item_rows):
        conn.executemany(
            "INSERT INTO orders (order_id, customer_id, store_id, order_timestamp, total_amount, num_items) VALUES (?,?,?,?,?,?)",
            order_rows,
        )
        conn.executemany(
            "INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, is_promo, discount_amount) VALUES (?,?,?,?,?,?,?)",
            item_rows,
        )
        conn.commit()

    def _get_seasonal_multiplier(self, day_of_year):
        mult = 1.0
        for event in SEASONAL_EVENTS.values():
            if event["start_day"] <= day_of_year <= event["end_day"]:
                mult = max(mult, event["multiplier"])
        return mult

    # ------------------------------------------------------------------
    # Offers
    # ------------------------------------------------------------------

    def _generate_offers(self, conn):
        products = self._products_df

        # Prefer products in popular categories for offers
        pop_cats = CATEGORY_NAMES[:10]  # Top 10 by weight
        pop_mask = products["category"].isin(pop_cats)
        offer_product_pool = products.loc[pop_mask, "product_id"].values

        if len(offer_product_pool) < self.n_offers:
            offer_product_pool = products["product_id"].values

        chosen_products = self.rng.choice(
            offer_product_pool, size=self.n_offers, replace=False
        )

        segments = list(SEGMENT_DIST.keys())
        rows = []

        for i in range(self.n_offers):
            oid = i + 1
            pid = int(chosen_products[i])

            # Discount type
            dtype = self.rng.choice(
                ["percentage", "fixed_amount", "bogo"], p=[0.60, 0.25, 0.15]
            )
            if dtype == "percentage":
                dvalue = round(float(self.rng.uniform(10, 40)), 0)
            elif dtype == "fixed_amount":
                dvalue = round(float(self.rng.uniform(1, 10)), 2)
            else:
                dvalue = 100.0  # BOGO

            # Stagger start dates across the history window
            # Ensure ~100 are active on any given day
            offer_duration = int(self.rng.integers(7, 29))
            latest_start = self.history_days - offer_duration
            start_offset = int(self.rng.integers(0, max(1, latest_start)))
            sdate = self.start_date + timedelta(days=start_offset)
            edate = sdate + timedelta(days=offer_duration)

            # Store scope
            store_scope = None
            if self.rng.random() < 0.30:
                n_scope = int(self.rng.integers(1, min(6, self.n_stores + 1)))
                stores = self.rng.choice(
                    range(1, self.n_stores + 1), size=n_scope, replace=False
                )
                store_scope = ",".join(str(s) for s in sorted(stores))

            # Segment scope
            segment_scope = None
            if self.rng.random() < 0.40:
                n_seg = int(self.rng.integers(1, len(segments)))
                segs = self.rng.choice(segments, size=n_seg, replace=False)
                segment_scope = ",".join(sorted(segs))

            max_redemptions = int(self.rng.integers(500, 5001))

            rows.append({
                "offer_id": oid,
                "product_id": pid,
                "discount_type": dtype,
                "discount_value": dvalue,
                "start_date": sdate.isoformat(),
                "end_date": edate.isoformat(),
                "store_scope": store_scope,
                "segment_scope": segment_scope,
                "max_redemptions": max_redemptions,
            })

        df = pd.DataFrame(rows)
        df.to_sql("offers", conn, if_exists="append", index=False)
        conn.commit()
        self._offers_df = df
        logger.info(f"  Created {len(df):,} offers")

    # ------------------------------------------------------------------
    # Impressions & Redemptions
    # ------------------------------------------------------------------

    def _generate_impressions_and_redemptions(self, conn):
        customers = self._customers_df
        offers = self._offers_df
        products = self._products_df

        # Pre-compute offer -> product info
        offer_product = {}
        for _, row in offers.iterrows():
            oid = row["offer_id"]
            pid = row["product_id"]
            prod_row = products.loc[products["product_id"] == pid].iloc[0]
            offer_product[oid] = {
                "product_id": pid,
                "category": prod_row["category"],
                "base_price": prod_row["base_price"],
                "discount_type": row["discount_type"],
                "discount_value": row["discount_value"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "segment_scope": row["segment_scope"],
                "store_scope": row["store_scope"],
            }

        # Pre-compute customer top categories from order_items
        logger.info("  Computing customer purchase history for impression generation...")
        cust_categories = self._compute_customer_categories(conn)
        cust_products = self._compute_customer_products(conn)

        # Pre-compute order lookup for redemption linking
        cust_orders = self._compute_customer_orders(conn)

        channels = ["email", "app", "in_store"]
        channel_weights = [0.40, 0.35, 0.25]

        impression_rows = []
        redemption_rows = []
        impression_id = 0
        redemption_id = 0

        # Process customers in batches
        impressions_per_customer = max(1, self.target_impressions // self.n_customers)

        for batch_start in tqdm(
            range(0, self.n_customers, 5000),
            desc="Generating impressions",
            unit="batch",
        ):
            batch_end = min(batch_start + 5000, self.n_customers)
            batch = customers.iloc[batch_start:batch_end]

            for _, cust in batch.iterrows():
                cid = cust["customer_id"]
                seg = cust["segment"]
                store_id = cust["home_store_id"]
                profile = SEGMENT_PROFILES[seg]
                cust_promo_aff = profile["promo_affinity"]
                cust_top_cats = cust_categories.get(cid, set())
                cust_prods = cust_products.get(cid, set())
                cust_order_list = cust_orders.get(cid, [])

                # How many impressions for this customer
                n_imp = max(
                    1,
                    int(
                        self.rng.poisson(impressions_per_customer)
                        * (1 + self.rng.normal(0, 0.3))
                    ),
                )

                for _ in range(n_imp):
                    # Pick a random day in the history window
                    day_offset = int(self.rng.integers(0, self.history_days))
                    imp_date = self.start_date + timedelta(days=day_offset)
                    imp_ts = datetime.combine(
                        imp_date, datetime.min.time()
                    ).replace(
                        hour=int(self.rng.integers(8, 21)),
                        minute=int(self.rng.integers(0, 60)),
                    )

                    # Pick an offer that was active on this date
                    active_offers = [
                        oid
                        for oid, info in offer_product.items()
                        if info["start_date"] <= imp_date.isoformat() <= info["end_date"]
                    ]
                    if not active_offers:
                        continue

                    # Bias toward offers in customer's preferred categories
                    offer_scores = []
                    for oid in active_offers:
                        info = offer_product[oid]
                        score = 1.0
                        if info["category"] in cust_top_cats:
                            score *= 3.0
                        # Check eligibility
                        if info["segment_scope"]:
                            if seg not in info["segment_scope"].split(","):
                                score = 0.0
                        if info["store_scope"]:
                            if str(store_id) not in info["store_scope"].split(","):
                                score *= 0.3
                        offer_scores.append(score)

                    offer_scores = np.array(offer_scores, dtype=float)
                    if offer_scores.sum() == 0:
                        continue
                    offer_scores /= offer_scores.sum()

                    chosen_oid = int(self.rng.choice(active_offers, p=offer_scores))
                    info = offer_product[chosen_oid]

                    impression_id += 1
                    channel = self.rng.choice(channels, p=channel_weights)

                    impression_rows.append((
                        impression_id,
                        cid,
                        chosen_oid,
                        imp_ts.isoformat(),
                        channel,
                    ))

                    # Determine if this impression leads to a redemption
                    redeem_prob = self._compute_redemption_prob(
                        info, cust_promo_aff, cust_top_cats, cust_prods, seg
                    )

                    if self.rng.random() < redeem_prob:
                        # Link to an order that happens after the impression
                        # Find the closest order after imp_date
                        linked_order_id = self._find_order_after(
                            cust_order_list, imp_date
                        )
                        if linked_order_id is None:
                            continue

                        redeem_delay = int(self.rng.integers(0, 8))  # 0-7 days
                        redeem_ts = imp_ts + timedelta(days=redeem_delay)
                        redemption_id += 1

                        redemption_rows.append((
                            redemption_id,
                            cid,
                            chosen_oid,
                            linked_order_id,
                            redeem_ts.isoformat(),
                        ))

            # Batch insert
            if len(impression_rows) > 100000:
                self._flush_impressions(
                    conn, impression_rows, redemption_rows
                )
                impression_rows.clear()
                redemption_rows.clear()

        # Final flush
        if impression_rows:
            self._flush_impressions(conn, impression_rows, redemption_rows)

        logger.info(
            f"  Created {impression_id:,} impressions and {redemption_id:,} redemptions "
            f"({redemption_id / max(1, impression_id) * 100:.1f}% conversion)"
        )

    def _compute_redemption_prob(
        self, offer_info, cust_promo_aff, cust_top_cats, cust_prods, segment
    ):
        """Compute P(redemption | impression) based on multiple signals."""
        base_rate = TARGET_REDEMPTION_RATE

        # Category affinity: 3x if customer buys this category
        cat_boost = 3.0 if offer_info["category"] in cust_top_cats else 0.7

        # Promo sensitivity
        promo_boost = 0.5 + 1.5 * cust_promo_aff

        # Discount depth
        if offer_info["discount_type"] == "percentage":
            depth = offer_info["discount_value"] / 100.0
        elif offer_info["discount_type"] == "fixed_amount":
            depth = min(1.0, offer_info["discount_value"] / max(0.01, offer_info["base_price"]))
        else:
            depth = 0.50  # BOGO

        depth_boost = 0.5 + 2.0 * depth

        # Prior purchase of the product
        prior_boost = 2.0 if offer_info["product_id"] in cust_prods else 0.8

        # Segment-discount alignment
        seg_profiles = SEGMENT_PROFILES[segment]
        sensitivity = seg_profiles["price_sensitivity"]
        alignment = 0.5 + sensitivity * depth * 2.0

        prob = base_rate * cat_boost * promo_boost * depth_boost * prior_boost * alignment
        return min(prob, 0.60)

    def _compute_customer_categories(self, conn):
        """Get top categories per customer from order history."""
        cursor = conn.execute("""
            SELECT o.customer_id, p.category, COUNT(*) as cnt
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            GROUP BY o.customer_id, p.category
        """)
        cust_cats = {}
        for row in cursor:
            cid = row[0]
            cat = row[1]
            cnt = row[2]
            if cid not in cust_cats:
                cust_cats[cid] = {}
            cust_cats[cid][cat] = cnt

        # Convert to top-3 category sets
        result = {}
        for cid, cat_dict in cust_cats.items():
            sorted_cats = sorted(cat_dict.items(), key=lambda x: -x[1])
            result[cid] = {c[0] for c in sorted_cats[:5]}
        return result

    def _compute_customer_products(self, conn):
        """Get set of product_ids each customer has purchased."""
        cursor = conn.execute("""
            SELECT DISTINCT o.customer_id, oi.product_id
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
        """)
        result = {}
        for row in cursor:
            cid = row[0]
            pid = row[1]
            if cid not in result:
                result[cid] = set()
            result[cid].add(pid)
        return result

    def _compute_customer_orders(self, conn):
        """Get list of (order_id, order_date) per customer, sorted by date."""
        cursor = conn.execute("""
            SELECT customer_id, order_id, DATE(order_timestamp) as odate
            FROM orders
            ORDER BY customer_id, order_timestamp
        """)
        result = {}
        for row in cursor:
            cid = row[0]
            if cid not in result:
                result[cid] = []
            result[cid].append((row[1], row[2]))
        return result

    def _find_order_after(self, order_list, after_date):
        """Find the first order_id after the given date."""
        target = after_date.isoformat()
        for order_id, odate in order_list:
            if odate >= target:
                return order_id
        # If no order after, use the last order
        if order_list:
            return order_list[-1][0]
        return None

    def _flush_impressions(self, conn, impression_rows, redemption_rows):
        conn.executemany(
            "INSERT INTO impressions (impression_id, customer_id, offer_id, shown_timestamp, channel) VALUES (?,?,?,?,?)",
            impression_rows,
        )
        conn.executemany(
            "INSERT INTO redemptions (redemption_id, customer_id, offer_id, order_id, redeemed_timestamp) VALUES (?,?,?,?,?)",
            redemption_rows,
        )
        conn.commit()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _print_summary(self, conn):
        tables = [
            "customers", "products", "orders", "order_items",
            "offers", "impressions", "redemptions",
        ]
        logger.info("=" * 50)
        logger.info("Data Generation Summary")
        logger.info("=" * 50)
        for t in tables:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            logger.info(f"  {t:20s}: {count:>12,}")

        # DB file size
        import os
        db_size = os.path.getsize(str(DB_PATH)) / (1024 * 1024)
        logger.info(f"  {'Database size':20s}: {db_size:>10.1f} MB")
        logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for Metro Recommender"
    )
    parser.add_argument("--customers", type=int, default=N_CUSTOMERS)
    parser.add_argument("--products", type=int, default=N_PRODUCTS)
    parser.add_argument("--offers", type=int, default=N_OFFERS)
    parser.add_argument("--stores", type=int, default=N_STORES)
    parser.add_argument("--days", type=int, default=HISTORY_DAYS)
    parser.add_argument("--target-items", type=int, default=TARGET_ORDER_ITEMS)
    parser.add_argument("--target-impressions", type=int, default=TARGET_IMPRESSIONS)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    generator = MetroDataGenerator(
        seed=args.seed,
        n_customers=args.customers,
        n_products=args.products,
        n_offers=args.offers,
        n_stores=args.stores,
        history_days=args.days,
        target_order_items=args.target_items,
        target_impressions=args.target_impressions,
    )
    generator.generate_all()


if __name__ == "__main__":
    main()
