-- Metro Romania Personalized Offers Recommender - Database Schema
-- B2B cash-and-carry wholesaler. All customers are registered businesses.
-- All prices in RON. Tiered pricing ("Staffelpreise") on every product.

-- =========================================================================
-- Core tables
-- =========================================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    business_name TEXT NOT NULL,
    business_type TEXT NOT NULL,        -- horeca, trader, sco, freelancer
    business_subtype TEXT NOT NULL,     -- restaurant, cafe_bar, grocery_store, etc.
    tax_id TEXT,                        -- CUI / CIF
    metro_card_number TEXT NOT NULL,
    card_issue_date DATE NOT NULL,
    home_store_id INTEGER NOT NULL,
    join_date DATE NOT NULL,
    loyalty_tier TEXT,                  -- classic, plus, star
    email_consent BOOLEAN DEFAULT 0,
    sms_consent BOOLEAN DEFAULT 0,
    app_registered BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    brand TEXT,
    is_own_brand BOOLEAN DEFAULT 0,
    own_brand_name TEXT,               -- metro_chef, aro, rioba, etc.
    tier1_price REAL NOT NULL,         -- single unit price (RON)
    tier2_price REAL,                  -- case quantity price
    tier2_min_qty INTEGER,             -- minimum qty for tier2
    tier3_price REAL,                  -- bulk/pallet price
    tier3_min_qty INTEGER,             -- minimum qty for tier3
    margin REAL,
    shelf_life_days INTEGER,
    unit_type TEXT DEFAULT 'buc',      -- buc, kg, l
    pack_size INTEGER DEFAULT 1,
    is_daily_price BOOLEAN DEFAULT 0,  -- Tagespreis for ultra-fresh
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    order_timestamp TIMESTAMP NOT NULL,
    total_amount REAL NOT NULL,
    total_amount_before_tier REAL,     -- amount if all items at tier1
    total_quantity INTEGER NOT NULL,
    num_items INTEGER NOT NULL,
    payment_method TEXT DEFAULT 'card',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,          -- actual price paid (tier-adjusted)
    tier_applied INTEGER DEFAULT 1,    -- 1, 2, or 3
    tier_savings REAL DEFAULT 0.0,     -- savings vs tier1 per unit
    is_promo BOOLEAN DEFAULT 0,
    discount_amount REAL DEFAULT 0.0,
    offer_id INTEGER,                  -- FK to offers if redeemed
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id)
);

CREATE TABLE IF NOT EXISTS offers (
    offer_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    offer_type TEXT NOT NULL,           -- percentage, fixed_amount, buy_x_get_y, volume_bonus, bundle, free_gift
    discount_value REAL NOT NULL,
    buy_quantity INTEGER,               -- for buy_x_get_y: buy X
    get_quantity INTEGER,               -- for buy_x_get_y: get Y free
    min_purchase_qty INTEGER,           -- minimum quantity to qualify
    min_purchase_amount REAL,           -- minimum RON to qualify
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    campaign_type TEXT,                 -- weekly_catalog, personalized, seasonal, etc.
    channel TEXT,                       -- email, app, catalog, sms, in_store
    store_scope TEXT,
    business_type_scope TEXT,           -- comma-separated: horeca,trader
    business_subtype_scope TEXT,        -- comma-separated: restaurant,cafe_bar
    loyalty_tier_scope TEXT,            -- comma-separated: plus,star
    max_redemptions INTEGER,
    max_per_customer INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS impressions (
    impression_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    shown_timestamp TIMESTAMP NOT NULL,
    channel TEXT,
    campaign_type TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id)
);

CREATE TABLE IF NOT EXISTS redemptions (
    redemption_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    redeemed_timestamp TIMESTAMP NOT NULL,
    channel TEXT,
    discount_amount_applied REAL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date DATE NOT NULL,
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    score REAL NOT NULL,
    rank INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_recommendations_unique
    ON recommendations(run_date, customer_id, offer_id);

-- =========================================================================
-- Feature tables (rebuilt by the pipeline)
-- =========================================================================

CREATE TABLE IF NOT EXISTS customer_features (
    customer_id INTEGER PRIMARY KEY,
    recency_days REAL,
    frequency INTEGER,
    monetary REAL,
    promo_affinity REAL,
    avg_basket_size REAL,
    avg_basket_quantity REAL,
    avg_order_value REAL,
    category_entropy REAL,
    top_3_categories TEXT,
    avg_discount_depth REAL,
    tier2_purchase_ratio REAL,
    tier3_purchase_ratio REAL,
    avg_tier_savings_pct REAL,
    fresh_category_ratio REAL,
    preferred_shopping_day INTEGER,
    days_between_visits_avg REAL,
    loyalty_tier TEXT,
    business_type TEXT,
    business_subtype TEXT,
    reference_date DATE
);

CREATE TABLE IF NOT EXISTS offer_features (
    offer_id INTEGER PRIMARY KEY,
    discount_depth REAL,
    margin_impact REAL,
    days_until_expiry INTEGER,
    historical_redemption_rate REAL,
    total_impressions INTEGER,
    total_redemptions INTEGER,
    category TEXT,
    brand TEXT,
    tier1_price REAL,
    is_own_brand INTEGER,
    offer_type TEXT,
    campaign_type TEXT,
    horeca_redemption_rate REAL,
    trader_redemption_rate REAL,
    reference_date DATE
);

CREATE TABLE IF NOT EXISTS candidate_pool (
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    strategy TEXT NOT NULL,
    run_date DATE NOT NULL,
    PRIMARY KEY (run_date, customer_id, offer_id)
);

-- =========================================================================
-- Monitoring tables
-- =========================================================================

CREATE TABLE IF NOT EXISTS drift_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date DATE NOT NULL,
    feature_name TEXT NOT NULL,
    psi_value REAL NOT NULL,
    severity TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date DATE NOT NULL,
    step TEXT NOT NULL,
    status TEXT NOT NULL,
    duration_seconds REAL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================================
-- Indexes for query performance
-- =========================================================================

CREATE INDEX IF NOT EXISTS idx_orders_customer_date
    ON orders(customer_id, order_timestamp);

CREATE INDEX IF NOT EXISTS idx_orders_timestamp
    ON orders(order_timestamp);

CREATE INDEX IF NOT EXISTS idx_order_items_order
    ON order_items(order_id);

CREATE INDEX IF NOT EXISTS idx_order_items_product
    ON order_items(product_id);

CREATE INDEX IF NOT EXISTS idx_order_items_tier
    ON order_items(tier_applied);

CREATE INDEX IF NOT EXISTS idx_impressions_customer_offer
    ON impressions(customer_id, offer_id);

CREATE INDEX IF NOT EXISTS idx_impressions_timestamp
    ON impressions(shown_timestamp);

CREATE INDEX IF NOT EXISTS idx_redemptions_customer_offer
    ON redemptions(customer_id, offer_id);

CREATE INDEX IF NOT EXISTS idx_redemptions_timestamp
    ON redemptions(redeemed_timestamp);

CREATE INDEX IF NOT EXISTS idx_recommendations_lookup
    ON recommendations(run_date, customer_id);

CREATE INDEX IF NOT EXISTS idx_offers_dates
    ON offers(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_offers_campaign_type
    ON offers(campaign_type);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category);

CREATE INDEX IF NOT EXISTS idx_products_own_brand
    ON products(is_own_brand);

CREATE INDEX IF NOT EXISTS idx_customers_business_type
    ON customers(business_type);

CREATE INDEX IF NOT EXISTS idx_customers_business_subtype
    ON customers(business_subtype);

CREATE INDEX IF NOT EXISTS idx_candidate_pool_date
    ON candidate_pool(run_date, customer_id);
