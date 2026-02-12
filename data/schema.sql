-- Metro Personalized Offers Recommender - Database Schema
-- All tables for the recommendation pipeline.

-- =========================================================================
-- Core tables
-- =========================================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    segment TEXT NOT NULL,
    home_store_id INTEGER NOT NULL,
    join_date DATE NOT NULL,
    loyalty_tier TEXT,
    email_consent BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    brand TEXT,
    base_price REAL NOT NULL,
    margin REAL,
    shelf_life_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    order_timestamp TIMESTAMP NOT NULL,
    total_amount REAL NOT NULL,
    num_items INTEGER NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    is_promo BOOLEAN DEFAULT 0,
    discount_amount REAL DEFAULT 0.0,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS offers (
    offer_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    discount_type TEXT NOT NULL,
    discount_value REAL NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    store_scope TEXT,
    segment_scope TEXT,
    max_redemptions INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS impressions (
    impression_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    shown_timestamp TIMESTAMP NOT NULL,
    channel TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id)
);

CREATE TABLE IF NOT EXISTS redemptions (
    redemption_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    redeemed_timestamp TIMESTAMP NOT NULL,
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
    category_entropy REAL,
    top_3_categories TEXT,
    avg_discount_depth REAL,
    loyalty_tier TEXT,
    segment TEXT,
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
    base_price REAL,
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

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category);

CREATE INDEX IF NOT EXISTS idx_candidate_pool_date
    ON candidate_pool(run_date, customer_id);
