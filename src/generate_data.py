"""
Synthetic data generator for Metro Romania Personalized Offers Recommender.

Generates realistic B2B wholesale data with:
  - Registered business customers (HoReCa, Traders, SCO, Freelancers)
  - Tiered pricing on every product (Staffelpreise)
  - Metro own brands and Romanian brands
  - Wholesale quantity patterns per business subtype
  - Seasonal and weekly cycles (Mon/Thu peaks for HoReCa)

Usage:
    python src/generate_data.py
    python src/generate_data.py --customers 1000 --products 500 --offers 50
"""

import argparse
import logging
import os
import sys
import time
import json
import math
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.config import (
    SEED, N_CUSTOMERS, N_PRODUCTS, N_OFFERS, N_STORES, HISTORY_DAYS,
    TARGET_ORDER_ITEMS, TARGET_IMPRESSIONS, TARGET_REDEMPTION_RATE,
    BUSINESS_TYPE_DIST, BUSINESS_SUBTYPE_DIST, LOYALTY_TIERS,
    CATEGORY_NAMES, CATEGORY_WEIGHTS, SUBCATEGORIES,
    CATEGORY_PRICE_RANGE, CATEGORY_MARGIN_RANGE, CATEGORY_SHELF_LIFE,
    FRESH_CATEGORIES, BUSINESS_PROFILES, BUSINESS_CATEGORY_AFFINITY,
    METRO_OWN_BRANDS, OWN_BRAND_PROBABILITY, ROMANIAN_BRANDS,
    BRANDS_PER_CATEGORY, SEASONAL_EVENTS, WEEKLY_PATTERNS,
    TIER_DISCOUNT_RANGES, TIER_QUANTITY_THRESHOLDS,
    OFFER_TYPE_DIST, CAMPAIGN_TYPE_DIST, CHANNEL_DIST,
    PURCHASE_MODE_DIST, INDIVIDUAL_PURCHASE_PROFILE,
    DB_PATH, DATA_DIR, MODELS_DIR, LOGS_DIR,
)
from src.db import get_connection, init_db

logger = logging.getLogger(__name__)


# Business name templates per type
_BUSINESS_NAME_TEMPLATES = {
    "restaurant": ["Restaurant {}", "Trattoria {}", "La Mama {}", "Casa {}", "Taverna {}"],
    "cafe_bar": ["Cafe {}", "Bar {}", "Coffee House {}", "Bistro {}"],
    "hotel": ["Hotel {}", "Pensiunea {}", "Vila {}"],
    "catering": ["Catering {}", "Events {}"],
    "fast_food": ["Fast Food {}", "Express {}", "Quick Bite {}"],
    "bakery_pastry": ["Brutaria {}", "Patiseria {}", "Cofetaria {}"],
    "ghost_kitchen": ["Cloud Kitchen {}", "Ghost Kitchen {}"],
    "grocery_store": ["Magazin {}", "Alimentara {}", "La Doi Pasi {}"],
    "convenience": ["Mini Market {}", "Non-Stop {}"],
    "specialty_food": ["Delicatese {}", "Gourmet {}"],
    "liquor_store": ["Vinoteca {}", "Spirits {}"],
    "general_retail": ["General {}", "Market {}"],
    "office": ["Birou {}", "Office {}"],
    "hospital_clinic": ["Clinica {}", "Spital {}"],
    "school_university": ["Scoala {}", "Universitatea {}"],
    "canteen": ["Cantina {}", "Mensa {}"],
    "other_org": ["Organizatia {}", "Asociatia {}"],
    "independent_pro": ["PFA {}", "Cabinet {}"],
    "small_business": ["SRL {}", "Firma {}"],
}


class MetroDataGenerator:
    """Generates realistic synthetic data for the Metro Romania recommendation pipeline."""

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

        self._print_summary(conn)
        elapsed = time.time() - t_total
        logger.info(f"Data generation completed in {elapsed:.1f}s")

        conn.close()

    # ------------------------------------------------------------------
    # Customers
    # ------------------------------------------------------------------

    def _generate_customers(self, conn):
        btype_names = list(BUSINESS_TYPE_DIST.keys())
        btype_probs = list(BUSINESS_TYPE_DIST.values())

        btype_arr = self.rng.choice(btype_names, size=self.n_customers, p=btype_probs)

        # Business subtypes
        subtype_arr = []
        for bt in btype_arr:
            subs = list(BUSINESS_SUBTYPE_DIST[bt].keys())
            sub_probs = list(BUSINESS_SUBTYPE_DIST[bt].values())
            subtype_arr.append(self.rng.choice(subs, p=sub_probs))

        # Loyalty tiers
        loyalty = []
        for bt in btype_arr:
            tiers = list(LOYALTY_TIERS[bt].keys())
            probs = list(LOYALTY_TIERS[bt].values())
            loyalty.append(self.rng.choice(tiers, p=probs))

        # Home store
        store_ids = self.rng.integers(1, self.n_stores + 1, size=self.n_customers)

        # Join dates (skewed toward recent)
        days_ago = self.rng.exponential(scale=365, size=self.n_customers).astype(int)
        days_ago = np.clip(days_ago, 30, 1095)
        join_dates = [
            (self.end_date - timedelta(days=int(d))).isoformat() for d in days_ago
        ]

        # Card issue dates (same as join or slightly before)
        card_issue_dates = [
            (self.end_date - timedelta(days=int(d) + int(self.rng.integers(0, 30)))).isoformat()
            for d in days_ago
        ]

        rows = []
        for i in range(self.n_customers):
            cid = i + 1
            bt = btype_arr[i]
            sub = subtype_arr[i]
            profile = BUSINESS_PROFILES[sub]

            # Business name
            templates = _BUSINESS_NAME_TEMPLATES.get(sub, ["Business {}"])
            tmpl = self.rng.choice(templates)
            bname = tmpl.format(cid)

            # Tax ID (CUI format)
            tax_id = f"RO{self.rng.integers(10000000, 99999999)}"

            # Metro card number
            card_num = f"MC{self.rng.integers(100000000, 999999999)}"

            # Consent flags (from profile)
            email_c = int(self.rng.random() < profile["email_consent_rate"])
            sms_c = int(self.rng.random() < profile["sms_consent_rate"])
            app_reg = int(self.rng.random() < profile["app_registered_rate"])

            rows.append({
                "customer_id": cid,
                "business_name": bname,
                "business_type": bt,
                "business_subtype": sub,
                "tax_id": tax_id,
                "metro_card_number": card_num,
                "card_issue_date": card_issue_dates[i],
                "home_store_id": int(store_ids[i]),
                "join_date": join_dates[i],
                "loyalty_tier": loyalty[i],
                "email_consent": email_c,
                "sms_consent": sms_c,
                "app_registered": app_reg,
            })

        df = pd.DataFrame(rows)
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

        # Build own-brand candidate mapping (category -> list of brand_names)
        own_brand_by_cat = {}
        for brand_name, info in METRO_OWN_BRANDS.items():
            for cat in info["categories"]:
                if cat not in own_brand_by_cat:
                    own_brand_by_cat[cat] = []
                own_brand_by_cat[cat].append(brand_name)

        rows = []
        for pid in range(1, self.n_products + 1):
            cat = categories[pid - 1]
            subcats = SUBCATEGORIES.get(cat, ["general"])
            subcat = self.rng.choice(subcats)

            # Determine if own brand
            is_own_brand = False
            own_brand_name = None
            brand = None

            if cat in own_brand_by_cat and self.rng.random() < OWN_BRAND_PROBABILITY:
                is_own_brand = True
                own_brand_name = self.rng.choice(own_brand_by_cat[cat])
                brand = own_brand_name.replace("_", " ").title()
            else:
                # Use Romanian brands if available, else generic
                rom_brands = ROMANIAN_BRANDS.get(cat, [])
                if rom_brands and self.rng.random() < 0.4:
                    brand = self.rng.choice(rom_brands)
                else:
                    brand_num = self.rng.integers(1, BRANDS_PER_CATEGORY + 1)
                    brand = f"{cat}_brand_{brand_num}"

            # Tier1 price (log-normal within category range, in RON)
            pmin, pmax = CATEGORY_PRICE_RANGE[cat]
            log_mean = (math.log(pmin) + math.log(pmax)) / 2
            log_std = (math.log(pmax) - math.log(pmin)) / 4
            tier1_price = float(np.exp(self.rng.normal(log_mean, log_std)))
            tier1_price = round(max(pmin, min(pmax * 1.5, tier1_price)), 2)

            # Own-brand price adjustment
            if is_own_brand:
                price_factor = METRO_OWN_BRANDS[own_brand_name]["price_factor"]
                tier1_price = round(tier1_price * price_factor, 2)

            # Tiered pricing
            tier_thresholds = TIER_QUANTITY_THRESHOLDS.get(
                cat, {"tier2_qty": 5, "tier3_qty": 20}
            )
            t2_disc_min, t2_disc_max = TIER_DISCOUNT_RANGES["tier2_discount"]
            t3_disc_min, t3_disc_max = TIER_DISCOUNT_RANGES["tier3_discount"]

            tier2_discount = float(self.rng.uniform(t2_disc_min, t2_disc_max))
            tier3_discount = float(self.rng.uniform(t3_disc_min, t3_disc_max))

            tier2_price = round(tier1_price * (1 - tier2_discount), 2)
            tier3_price = round(tier1_price * (1 - tier3_discount), 2)
            tier2_min_qty = tier_thresholds["tier2_qty"]
            tier3_min_qty = tier_thresholds["tier3_qty"]

            # Margin
            mmin, mmax = CATEGORY_MARGIN_RANGE[cat]
            margin = round(float(self.rng.uniform(mmin, mmax)), 3)
            if is_own_brand:
                margin_factor = METRO_OWN_BRANDS[own_brand_name]["margin_factor"]
                margin = round(margin * margin_factor, 3)

            # Shelf life
            sl_min, sl_max = CATEGORY_SHELF_LIFE[cat]
            shelf_life = int(self.rng.integers(sl_min, sl_max + 1))

            # Unit type
            if cat in ("meat_poultry", "seafood", "fruits_vegetables", "deli_charcuterie"):
                unit_type = self.rng.choice(["buc", "kg"], p=[0.4, 0.6])
            elif cat in ("beverages_non_alcoholic", "beverages_alcoholic", "dairy_eggs"):
                unit_type = self.rng.choice(["buc", "l"], p=[0.7, 0.3])
            else:
                unit_type = "buc"

            pack_size = int(self.rng.choice([1, 1, 1, 6, 12]))
            is_daily_price = 1 if cat in FRESH_CATEGORIES and self.rng.random() < 0.3 else 0

            name = f"{brand}_{subcat}_{pid}"

            rows.append({
                "product_id": pid,
                "name": name,
                "category": cat,
                "subcategory": subcat,
                "brand": brand,
                "is_own_brand": int(is_own_brand),
                "own_brand_name": own_brand_name,
                "tier1_price": tier1_price,
                "tier2_price": tier2_price,
                "tier2_min_qty": tier2_min_qty,
                "tier3_price": tier3_price,
                "tier3_min_qty": tier3_min_qty,
                "margin": margin,
                "shelf_life_days": shelf_life,
                "unit_type": unit_type,
                "pack_size": pack_size,
                "is_daily_price": is_daily_price,
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

        # Product info for fast lookup
        product_info = {}
        for _, p in products.iterrows():
            product_info[p["product_id"]] = {
                "tier1_price": p["tier1_price"],
                "tier2_price": p["tier2_price"],
                "tier2_min_qty": p["tier2_min_qty"],
                "tier3_price": p["tier3_price"],
                "tier3_min_qty": p["tier3_min_qty"],
                "category": p["category"],
            }

        total_items = 0
        order_id = 0
        order_item_id = 0

        order_rows = []
        item_rows = []

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
                bt = cust["business_type"]
                sub = cust["business_subtype"]
                store_id = cust["home_store_id"]
                profile = BUSINESS_PROFILES[sub]

                # Customer-specific purchase frequency with noise
                freq = profile["purchase_freq_weekly"] * (
                    1 + self.rng.normal(0, 0.25)
                )
                freq = max(0.1, freq)

                # Customer-specific category affinity
                cat_affinity = np.array(CATEGORY_WEIGHTS, dtype=float)
                sub_aff = BUSINESS_CATEGORY_AFFINITY.get(sub, {})
                for i, cat_name in enumerate(CATEGORY_NAMES):
                    cat_affinity[i] *= sub_aff.get(cat_name, 1.0)
                cat_affinity *= (1 + self.rng.normal(0, 0.2, size=n_cats))
                cat_affinity = np.maximum(cat_affinity, 0.001)
                cat_affinity /= cat_affinity.sum()

                # Customer promo affinity
                cust_promo_aff = max(
                    0.0,
                    min(1.0, profile["promo_affinity"] + self.rng.normal(0, 0.1)),
                )

                # Generate order timestamps
                avg_orders = freq * (self.history_days / 7.0)
                n_orders = max(1, int(self.rng.poisson(avg_orders)))

                order_days = self.rng.integers(0, self.history_days, size=n_orders)
                order_days.sort()

                for day_offset in order_days:
                    order_date = self.start_date + timedelta(days=int(day_offset))
                    dow = order_date.weekday()
                    doy = order_date.timetuple().tm_yday

                    # Weekly pattern by business type
                    weekly_mult = WEEKLY_PATTERNS.get(bt, {}).get(dow, 1.0)

                    # Seasonal
                    seasonal_mult = self._get_seasonal_multiplier(doy)

                    accept_prob = min(1.0, weekly_mult * seasonal_mult * 0.6)
                    if self.rng.random() > accept_prob:
                        continue

                    order_id += 1

                    # Determine purchase mode: business (~87%) or individual (~13%)
                    purchase_mode = self.rng.choice(
                        list(PURCHASE_MODE_DIST.keys()),
                        p=list(PURCHASE_MODE_DIST.values()),
                    )
                    is_individual = purchase_mode == "individual"

                    # Basket size (varies by subtype; much smaller for individual)
                    basket_mean = profile["basket_size_mean"]
                    basket_std = profile["basket_size_std"]
                    if is_individual:
                        basket_mean = max(3, int(basket_mean * INDIVIDUAL_PURCHASE_PROFILE["basket_size_multiplier"]))
                        basket_std = max(2, int(basket_std * 0.5))
                    n_items = max(1, int(self.rng.normal(basket_mean, basket_std)))

                    # Select products
                    chosen_cats = self.rng.choice(
                        CATEGORY_NAMES, size=n_items, p=cat_affinity
                    )

                    order_total = 0.0
                    order_total_before_tier = 0.0
                    order_total_qty = 0
                    items_in_this_order = 0

                    for chosen_cat in chosen_cats:
                        prods_in_cat = cat_to_products.get(chosen_cat)
                        if prods_in_cat is None or len(prods_in_cat) == 0:
                            continue

                        prod_id = int(self.rng.choice(prods_in_cat))
                        pinfo = product_info[prod_id]

                        # Quantities depend on purchase mode
                        if is_individual:
                            # Household quantities — 1-3 units, almost always tier 1
                            lo, hi = INDIVIDUAL_PURCHASE_PROFILE["quantity_range"]
                            quantity = int(self.rng.integers(lo, hi + 1))
                        else:
                            # Wholesale quantities by business type
                            quantity = self._get_wholesale_quantity(bt, sub, chosen_cat)

                        # Determine tier applied
                        tier_applied = 1
                        unit_price = pinfo["tier1_price"]
                        if is_individual:
                            # Individual purchases rarely hit tier thresholds
                            r = self.rng.random()
                            if r < INDIVIDUAL_PURCHASE_PROFILE["tier3_probability"] and quantity >= pinfo["tier3_min_qty"]:
                                tier_applied = 3
                                unit_price = pinfo["tier3_price"]
                            elif r < INDIVIDUAL_PURCHASE_PROFILE["tier2_probability"] and quantity >= pinfo["tier2_min_qty"]:
                                tier_applied = 2
                                unit_price = pinfo["tier2_price"]
                        else:
                            if quantity >= pinfo["tier3_min_qty"]:
                                tier_applied = 3
                                unit_price = pinfo["tier3_price"]
                            elif quantity >= pinfo["tier2_min_qty"]:
                                tier_applied = 2
                                unit_price = pinfo["tier2_price"]

                        # Small price variation
                        unit_price = round(
                            unit_price * (1 + self.rng.normal(0, 0.02)), 2
                        )
                        unit_price = max(0.50, unit_price)

                        tier_savings = round(pinfo["tier1_price"] - unit_price, 2)
                        tier_savings = max(0.0, tier_savings)

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
                            tier_applied,
                            tier_savings,
                            is_promo,
                            discount_amt,
                            None,  # offer_id
                        ))
                        line_total = (unit_price - discount_amt) * quantity
                        order_total += line_total
                        order_total_before_tier += pinfo["tier1_price"] * quantity
                        order_total_qty += quantity
                        items_in_this_order += 1

                    if items_in_this_order == 0:
                        order_id -= 1
                        continue

                    hour = int(self.rng.choice([6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17]))
                    minute = int(self.rng.integers(0, 60))
                    ts = datetime.combine(
                        order_date, datetime.min.time()
                    ).replace(hour=hour, minute=minute)

                    payment = self.rng.choice(
                        ["card", "cash", "transfer"], p=[0.50, 0.30, 0.20]
                    )

                    order_rows.append((
                        order_id,
                        cid,
                        store_id,
                        ts.isoformat(),
                        round(order_total, 2),
                        round(order_total_before_tier, 2),
                        order_total_qty,
                        items_in_this_order,
                        purchase_mode,
                        payment,
                    ))

                    total_items += items_in_this_order

            # Batch insert periodically
            if len(order_rows) > 50000:
                self._flush_orders(conn, order_rows, item_rows)
                order_rows.clear()
                item_rows.clear()

            if total_items >= self.target_order_items:
                break

        # Final flush
        if order_rows:
            self._flush_orders(conn, order_rows, item_rows)

        logger.info(f"  Created {order_id:,} orders with {total_items:,} items")
        self._total_orders = order_id

    def _get_wholesale_quantity(self, business_type, subtype, category):
        """Generate realistic wholesale quantities per business type and category."""
        if business_type == "horeca":
            if category in FRESH_CATEGORIES:
                qty = int(self.rng.choice([3, 5, 8, 10, 15, 20]))
            elif category in ("beverages_non_alcoholic", "beverages_alcoholic"):
                qty = int(self.rng.choice([6, 12, 24, 48]))
            elif category in ("cleaning_detergents", "paper_packaging"):
                qty = int(self.rng.choice([4, 6, 12, 24]))
            elif category == "horeca_equipment":
                qty = int(self.rng.choice([1, 1, 2]))
            else:
                qty = int(self.rng.choice([3, 5, 6, 10, 12]))
        elif business_type == "trader":
            if category in FRESH_CATEGORIES:
                qty = int(self.rng.choice([5, 10, 15, 20]))
            elif category in ("beverages_non_alcoholic", "beverages_alcoholic"):
                qty = int(self.rng.choice([12, 24, 48, 96]))
            elif category in ("confectionery_snacks", "grocery_staples"):
                qty = int(self.rng.choice([6, 12, 24, 48]))
            else:
                qty = int(self.rng.choice([3, 6, 12, 24]))
        elif business_type == "sco":
            if category in ("office_supplies", "paper_packaging"):
                qty = int(self.rng.choice([5, 10, 20, 50]))
            elif category in ("cleaning_detergents",):
                qty = int(self.rng.choice([6, 12, 24]))
            elif category in FRESH_CATEGORIES:
                qty = int(self.rng.choice([3, 5, 10]))
            else:
                qty = int(self.rng.choice([2, 3, 5, 10]))
        else:  # freelancer
            qty = int(self.rng.choice([1, 1, 2, 3, 5]))

        return qty

    def _flush_orders(self, conn, order_rows, item_rows):
        conn.executemany(
            "INSERT INTO orders (order_id, customer_id, store_id, order_timestamp, total_amount, total_amount_before_tier, total_quantity, num_items, purchase_mode, payment_method) VALUES (?,?,?,?,?,?,?,?,?,?)",
            order_rows,
        )
        conn.executemany(
            "INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, tier_applied, tier_savings, is_promo, discount_amount, offer_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
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
        pop_cats = CATEGORY_NAMES[:10]
        pop_mask = products["category"].isin(pop_cats)
        offer_product_pool = products.loc[pop_mask, "product_id"].values

        if len(offer_product_pool) < self.n_offers:
            offer_product_pool = products["product_id"].values

        chosen_products = self.rng.choice(
            offer_product_pool, size=self.n_offers, replace=False
        )

        btypes = list(BUSINESS_TYPE_DIST.keys())
        offer_types = list(OFFER_TYPE_DIST.keys())
        offer_type_probs = list(OFFER_TYPE_DIST.values())
        campaign_types = list(CAMPAIGN_TYPE_DIST.keys())
        campaign_probs = list(CAMPAIGN_TYPE_DIST.values())
        channels = list(CHANNEL_DIST.keys())
        channel_probs = list(CHANNEL_DIST.values())

        rows = []
        for i in range(self.n_offers):
            oid = i + 1
            pid = int(chosen_products[i])

            # Offer type
            otype = self.rng.choice(offer_types, p=offer_type_probs)

            # Discount value based on type
            buy_qty = None
            get_qty = None
            min_purchase_qty = None
            min_purchase_amount = None

            if otype == "percentage":
                dvalue = round(float(self.rng.uniform(10, 40)), 0)
            elif otype == "fixed_amount":
                dvalue = round(float(self.rng.uniform(5, 50)), 2)  # RON
            elif otype == "buy_x_get_y":
                buy_qty = int(self.rng.choice([3, 5, 6, 10]))
                get_qty = int(self.rng.choice([1, 1, 2]))
                dvalue = 100.0  # 100% off the free item
            elif otype == "volume_bonus":
                min_purchase_qty = int(self.rng.choice([6, 10, 12, 24]))
                dvalue = round(float(self.rng.uniform(5, 20)), 0)
            elif otype == "bundle":
                min_purchase_amount = round(float(self.rng.uniform(100, 500)), 0)
                dvalue = round(float(self.rng.uniform(5, 15)), 0)
            else:  # free_gift
                min_purchase_amount = round(float(self.rng.uniform(200, 1000)), 0)
                dvalue = 0.0

            # Campaign type
            ctype = self.rng.choice(campaign_types, p=campaign_probs)
            channel = self.rng.choice(channels, p=channel_probs)

            # Stagger start dates
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

            # Business type scope
            btype_scope = None
            if self.rng.random() < 0.40:
                n_bt = int(self.rng.integers(1, len(btypes)))
                chosen_bt = self.rng.choice(btypes, size=n_bt, replace=False)
                btype_scope = ",".join(sorted(chosen_bt))

            # Loyalty tier scope
            ltier_scope = None
            if self.rng.random() < 0.20:
                ltier_scope = self.rng.choice(
                    ["plus,star", "star"], p=[0.7, 0.3]
                )

            max_redemptions = int(self.rng.integers(500, 5001))
            max_per_customer = int(self.rng.choice([1, 1, 2, 3, 5]))

            rows.append({
                "offer_id": oid,
                "product_id": pid,
                "offer_type": otype,
                "discount_value": dvalue,
                "buy_quantity": buy_qty,
                "get_quantity": get_qty,
                "min_purchase_qty": min_purchase_qty,
                "min_purchase_amount": min_purchase_amount,
                "start_date": sdate.isoformat(),
                "end_date": edate.isoformat(),
                "campaign_type": ctype,
                "channel": channel,
                "store_scope": store_scope,
                "business_type_scope": btype_scope,
                "business_subtype_scope": None,
                "loyalty_tier_scope": ltier_scope,
                "max_redemptions": max_redemptions,
                "max_per_customer": max_per_customer,
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
                "tier1_price": prod_row["tier1_price"],
                "offer_type": row["offer_type"],
                "discount_value": row["discount_value"],
                "start_date": row["start_date"],
                "end_date": row["end_date"],
                "business_type_scope": row["business_type_scope"],
                "store_scope": row["store_scope"],
                "campaign_type": row.get("campaign_type"),
            }

        # Pre-compute customer purchase history
        logger.info("  Computing customer purchase history for impression generation...")
        cust_categories = self._compute_customer_categories(conn)
        cust_products = self._compute_customer_products(conn)
        cust_orders = self._compute_customer_orders(conn)

        channels = list(CHANNEL_DIST.keys())
        channel_weights = list(CHANNEL_DIST.values())

        impression_rows = []
        redemption_rows = []
        impression_id = 0
        redemption_id = 0

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
                bt = cust["business_type"]
                sub = cust["business_subtype"]
                store_id = cust["home_store_id"]
                profile = BUSINESS_PROFILES[sub]
                cust_promo_aff = profile["promo_affinity"]
                cust_top_cats = cust_categories.get(cid, set())
                cust_prods = cust_products.get(cid, set())
                cust_order_list = cust_orders.get(cid, [])

                n_imp = max(
                    1,
                    int(
                        self.rng.poisson(impressions_per_customer)
                        * (1 + self.rng.normal(0, 0.3))
                    ),
                )

                for _ in range(n_imp):
                    day_offset = int(self.rng.integers(0, self.history_days))
                    imp_date = self.start_date + timedelta(days=day_offset)
                    imp_ts = datetime.combine(
                        imp_date, datetime.min.time()
                    ).replace(
                        hour=int(self.rng.integers(8, 21)),
                        minute=int(self.rng.integers(0, 60)),
                    )

                    # Pick an offer active on this date
                    active_offers = [
                        oid
                        for oid, info in offer_product.items()
                        if info["start_date"] <= imp_date.isoformat() <= info["end_date"]
                    ]
                    if not active_offers:
                        continue

                    # Score offers for this customer
                    offer_scores = []
                    for oid in active_offers:
                        info = offer_product[oid]
                        score = 1.0
                        if info["category"] in cust_top_cats:
                            score *= 3.0
                        # Check business type eligibility
                        if info["business_type_scope"]:
                            if bt not in info["business_type_scope"].split(","):
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
                    ctype = info.get("campaign_type")

                    impression_rows.append((
                        impression_id,
                        cid,
                        chosen_oid,
                        imp_ts.isoformat(),
                        channel,
                        ctype,
                    ))

                    # Determine redemption
                    redeem_prob = self._compute_redemption_prob(
                        info, cust_promo_aff, cust_top_cats, cust_prods, bt, sub
                    )

                    if self.rng.random() < redeem_prob:
                        linked_order_id = self._find_order_after(
                            cust_order_list, imp_date
                        )
                        if linked_order_id is None:
                            continue

                        redeem_delay = int(self.rng.integers(0, 8))
                        redeem_ts = imp_ts + timedelta(days=redeem_delay)
                        redemption_id += 1

                        # Compute discount amount
                        disc_applied = self._compute_discount_amount(info)

                        redemption_rows.append((
                            redemption_id,
                            cid,
                            chosen_oid,
                            linked_order_id,
                            redeem_ts.isoformat(),
                            channel,
                            disc_applied,
                        ))

            # Batch insert
            if len(impression_rows) > 100000:
                self._flush_impressions(conn, impression_rows, redemption_rows)
                impression_rows.clear()
                redemption_rows.clear()

        # Final flush
        if impression_rows:
            self._flush_impressions(conn, impression_rows, redemption_rows)

        logger.info(
            f"  Created {impression_id:,} impressions and {redemption_id:,} redemptions "
            f"({redemption_id / max(1, impression_id) * 100:.1f}% conversion)"
        )

    def _compute_discount_amount(self, offer_info):
        """Compute approximate discount amount in RON for a redemption."""
        otype = offer_info["offer_type"]
        dvalue = offer_info["discount_value"]
        price = offer_info["tier1_price"]

        if otype == "percentage":
            return round(price * dvalue / 100.0, 2)
        elif otype == "fixed_amount":
            return round(min(dvalue, price), 2)
        elif otype == "buy_x_get_y":
            return round(price, 2)  # one free item
        elif otype == "volume_bonus":
            return round(price * dvalue / 100.0, 2)
        elif otype == "bundle":
            return round(dvalue, 2)
        else:  # free_gift
            return 0.0

    def _compute_redemption_prob(
        self, offer_info, cust_promo_aff, cust_top_cats, cust_prods,
        business_type, business_subtype
    ):
        """Compute P(redemption | impression) based on multiple signals."""
        base_rate = TARGET_REDEMPTION_RATE

        # Category affinity
        cat_boost = 3.0 if offer_info["category"] in cust_top_cats else 0.7

        # Promo sensitivity
        promo_boost = 0.5 + 1.5 * cust_promo_aff

        # Discount depth
        otype = offer_info["offer_type"]
        dvalue = offer_info["discount_value"]
        price = offer_info["tier1_price"]

        if otype == "percentage":
            depth = dvalue / 100.0
        elif otype == "fixed_amount":
            depth = min(1.0, dvalue / max(0.01, price))
        elif otype == "buy_x_get_y":
            depth = 0.50
        elif otype == "volume_bonus":
            depth = dvalue / 100.0
        elif otype == "bundle":
            depth = 0.30
        else:
            depth = 0.20

        depth_boost = 0.5 + 2.0 * depth

        # Prior purchase
        prior_boost = 2.0 if offer_info["product_id"] in cust_prods else 0.8

        # Business type price sensitivity
        profile = BUSINESS_PROFILES.get(business_subtype, {})
        sensitivity = profile.get("price_sensitivity", 0.5)
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
        if order_list:
            return order_list[-1][0]
        return None

    def _flush_impressions(self, conn, impression_rows, redemption_rows):
        conn.executemany(
            "INSERT INTO impressions (impression_id, customer_id, offer_id, shown_timestamp, channel, campaign_type) VALUES (?,?,?,?,?,?)",
            impression_rows,
        )
        conn.executemany(
            "INSERT INTO redemptions (redemption_id, customer_id, offer_id, order_id, redeemed_timestamp, channel, discount_amount_applied) VALUES (?,?,?,?,?,?,?)",
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

        # Business type breakdown
        cursor = conn.execute(
            "SELECT business_type, COUNT(*) FROM customers GROUP BY business_type ORDER BY COUNT(*) DESC"
        )
        logger.info("  Business types:")
        for row in cursor:
            logger.info(f"    {row[0]:15s}: {row[1]:>8,}")

        # Purchase mode
        cursor = conn.execute(
            "SELECT purchase_mode, COUNT(*) FROM orders GROUP BY purchase_mode ORDER BY COUNT(*) DESC"
        )
        logger.info("  Purchase mode:")
        for row in cursor:
            logger.info(f"    {row[0]:15s}: {row[1]:>8,}")

        # Tier usage
        cursor = conn.execute(
            "SELECT tier_applied, COUNT(*) FROM order_items GROUP BY tier_applied ORDER BY tier_applied"
        )
        logger.info("  Tier usage:")
        for row in cursor:
            logger.info(f"    Tier {row[0]}: {row[1]:>10,}")

        import os
        db_size = os.path.getsize(str(DB_PATH)) / (1024 * 1024)
        logger.info(f"  {'Database size':20s}: {db_size:>10.1f} MB")
        logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for Metro Romania Recommender"
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
