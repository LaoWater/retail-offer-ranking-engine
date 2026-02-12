"""
Configuration for Metro Personalized Offers Recommender.
Single source of truth for all paths, hyperparameters, and constants.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "metro.db"
SCHEMA_PATH = DATA_DIR / "schema.sql"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42

# ---------------------------------------------------------------------------
# Data generation parameters
# ---------------------------------------------------------------------------
N_CUSTOMERS = 50_000
N_PRODUCTS = 10_000
N_OFFERS = 200
N_STORES = 50
HISTORY_DAYS = 180
TARGET_ORDER_ITEMS = 2_000_000
TARGET_IMPRESSIONS = 500_000
TARGET_REDEMPTION_RATE = 0.05  # 5% of impressions

# Segment distribution
SEGMENT_DIST = {
    "budget": 0.40,
    "premium": 0.20,
    "family": 0.30,
    "horeca": 0.10,
}

# Loyalty tier distribution by segment
LOYALTY_TIERS = {
    "budget":  {"bronze": 0.70, "silver": 0.25, "gold": 0.05},
    "premium": {"bronze": 0.10, "silver": 0.30, "gold": 0.60},
    "family":  {"bronze": 0.30, "silver": 0.50, "gold": 0.20},
    "horeca":  {"bronze": 0.40, "silver": 0.40, "gold": 0.20},
}

# 20 product categories with base frequency weights
CATEGORIES = [
    ("dairy", 0.12),
    ("produce", 0.11),
    ("bakery", 0.09),
    ("meat", 0.08),
    ("beverages", 0.08),
    ("frozen", 0.07),
    ("snacks", 0.06),
    ("household", 0.06),
    ("personal_care", 0.05),
    ("canned_goods", 0.04),
    ("condiments", 0.04),
    ("seafood", 0.03),
    ("deli", 0.03),
    ("baby", 0.03),
    ("pet", 0.02),
    ("alcohol", 0.02),
    ("organic", 0.02),
    ("international", 0.02),
    ("bulk", 0.02),
    ("seasonal", 0.01),
]

CATEGORY_NAMES = [c[0] for c in CATEGORIES]
CATEGORY_WEIGHTS = [c[1] for c in CATEGORIES]

# Subcategories per category
SUBCATEGORIES = {
    "dairy": ["milk", "cheese", "yogurt", "butter", "cream"],
    "produce": ["fruits", "vegetables", "herbs", "salads"],
    "bakery": ["bread", "pastries", "cakes", "rolls"],
    "meat": ["beef", "chicken", "pork", "lamb", "sausages"],
    "beverages": ["water", "juice", "soda", "coffee", "tea"],
    "frozen": ["frozen_meals", "ice_cream", "frozen_veg", "frozen_pizza"],
    "snacks": ["chips", "crackers", "nuts", "cookies", "candy"],
    "household": ["cleaning", "paper", "storage", "laundry"],
    "personal_care": ["shampoo", "soap", "dental", "skincare"],
    "canned_goods": ["beans", "soup", "tomatoes", "tuna", "vegetables"],
    "condiments": ["ketchup", "mustard", "mayo", "sauces", "spices"],
    "seafood": ["fish", "shrimp", "crab", "salmon"],
    "deli": ["ham", "salami", "cheese_deli", "olives"],
    "baby": ["formula", "diapers", "baby_food", "wipes"],
    "pet": ["dog_food", "cat_food", "treats", "accessories"],
    "alcohol": ["beer", "wine", "spirits", "mixers"],
    "organic": ["organic_produce", "organic_dairy", "organic_grains"],
    "international": ["asian", "mexican", "italian", "middle_eastern"],
    "bulk": ["rice", "flour", "oil", "sugar", "pasta"],
    "seasonal": ["holiday", "bbq", "summer", "winter"],
}

# Base price ranges by category (min, max in euros)
CATEGORY_PRICE_RANGE = {
    "dairy": (0.80, 8.00),
    "produce": (0.50, 6.00),
    "bakery": (0.60, 5.00),
    "meat": (3.00, 25.00),
    "beverages": (0.50, 8.00),
    "frozen": (1.50, 10.00),
    "snacks": (0.80, 6.00),
    "household": (1.00, 15.00),
    "personal_care": (1.50, 12.00),
    "canned_goods": (0.60, 4.00),
    "condiments": (0.80, 6.00),
    "seafood": (4.00, 30.00),
    "deli": (2.00, 12.00),
    "baby": (3.00, 25.00),
    "pet": (2.00, 20.00),
    "alcohol": (1.50, 40.00),
    "organic": (1.50, 15.00),
    "international": (1.00, 10.00),
    "bulk": (1.00, 8.00),
    "seasonal": (2.00, 20.00),
}

# Margin ranges by category (min, max as fraction)
CATEGORY_MARGIN_RANGE = {
    "dairy": (0.08, 0.20),
    "produce": (0.10, 0.30),
    "bakery": (0.15, 0.40),
    "meat": (0.06, 0.18),
    "beverages": (0.12, 0.35),
    "frozen": (0.10, 0.25),
    "snacks": (0.15, 0.40),
    "household": (0.12, 0.30),
    "personal_care": (0.15, 0.35),
    "canned_goods": (0.10, 0.25),
    "condiments": (0.12, 0.30),
    "seafood": (0.06, 0.15),
    "deli": (0.10, 0.25),
    "baby": (0.08, 0.20),
    "pet": (0.10, 0.25),
    "alcohol": (0.15, 0.40),
    "organic": (0.12, 0.30),
    "international": (0.12, 0.28),
    "bulk": (0.05, 0.15),
    "seasonal": (0.15, 0.45),
}

# Shelf life by category (days)
CATEGORY_SHELF_LIFE = {
    "dairy": (7, 30),
    "produce": (3, 14),
    "bakery": (2, 7),
    "meat": (3, 10),
    "beverages": (90, 365),
    "frozen": (90, 365),
    "snacks": (60, 365),
    "household": (365, 1095),
    "personal_care": (180, 730),
    "canned_goods": (365, 1095),
    "condiments": (180, 730),
    "seafood": (2, 7),
    "deli": (5, 14),
    "baby": (90, 365),
    "pet": (180, 730),
    "alcohol": (365, 3650),
    "organic": (3, 21),
    "international": (60, 365),
    "bulk": (90, 365),
    "seasonal": (30, 180),
}

# Segment behavioral profiles
SEGMENT_PROFILES = {
    "budget": {
        "purchase_freq_weekly": 0.8,
        "basket_size_mean": 8,
        "basket_size_std": 3,
        "promo_affinity": 0.65,
        "price_sensitivity": 0.85,
        "email_consent_rate": 0.60,
    },
    "premium": {
        "purchase_freq_weekly": 1.5,
        "basket_size_mean": 14,
        "basket_size_std": 5,
        "promo_affinity": 0.15,
        "price_sensitivity": 0.20,
        "email_consent_rate": 0.80,
    },
    "family": {
        "purchase_freq_weekly": 1.3,
        "basket_size_mean": 18,
        "basket_size_std": 6,
        "promo_affinity": 0.40,
        "price_sensitivity": 0.55,
        "email_consent_rate": 0.75,
    },
    "horeca": {
        "purchase_freq_weekly": 2.5,
        "basket_size_mean": 50,
        "basket_size_std": 20,
        "promo_affinity": 0.10,
        "price_sensitivity": 0.30,
        "email_consent_rate": 0.50,
    },
}

# Category affinity multipliers by segment (>1 = prefers, <1 = avoids)
SEGMENT_CATEGORY_AFFINITY = {
    "budget": {
        "snacks": 2.0, "canned_goods": 2.0, "frozen": 1.8,
        "beverages": 1.5, "bulk": 1.5,
        "organic": 0.3, "seafood": 0.4, "alcohol": 0.5,
    },
    "premium": {
        "organic": 3.0, "seafood": 2.5, "alcohol": 2.5,
        "deli": 2.0, "international": 1.8,
        "canned_goods": 0.4, "frozen": 0.5, "bulk": 0.3,
    },
    "family": {
        "dairy": 2.5, "bakery": 2.0, "baby": 3.0,
        "produce": 1.8, "snacks": 1.5,
        "alcohol": 0.2, "bulk": 0.5,
    },
    "horeca": {
        "bulk": 5.0, "meat": 2.5, "beverages": 2.0,
        "condiments": 2.0, "dairy": 1.5,
        "baby": 0.1, "pet": 0.1, "personal_care": 0.2,
    },
}

# Brands per category (mix of premium and store brands)
BRANDS_PER_CATEGORY = 8

# Seasonal multipliers (day_of_year -> multiplier)
SEASONAL_EVENTS = {
    # Christmas build-up (Dec 10-24, days 344-358)
    "christmas": {"start_day": 344, "end_day": 358, "multiplier": 2.5},
    # Easter (approx Apr 1-15, days 91-105)
    "easter": {"start_day": 91, "end_day": 105, "multiplier": 1.8},
    # Summer BBQ (Jul-Aug, days 182-243)
    "summer_bbq": {"start_day": 182, "end_day": 243, "multiplier": 1.3},
    # New Year (Jan 1-5, days 1-5)
    "new_year": {"start_day": 1, "end_day": 5, "multiplier": 1.5},
}

# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------
CANDIDATE_POOL_SIZE = 200
CANDIDATE_STRATEGY_LIMITS = {
    "category_affinity": 80,
    "segment_popular": 60,
    "repeat_purchase": 40,
    "high_margin": 20,
}

# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------
TOP_N_RECOMMENDATIONS = 10
NEGATIVE_SAMPLE_RATIO = 4
TRAIN_TEST_SPLIT = 0.2
RETRAIN_DAY_OF_WEEK = 0  # Monday
REDEMPTION_WINDOW_DAYS = 7

# Feature columns used by the ranker
FEATURE_COLUMNS = [
    "recency_days",
    "frequency",
    "monetary",
    "promo_affinity",
    "avg_basket_size",
    "category_entropy",
    "avg_discount_depth",
    "discount_depth",
    "margin_impact",
    "days_until_expiry",
    "historical_redemption_rate",
    "bought_product_before",
    "days_since_last_cat_purchase",
    "category_affinity_score",
    "discount_depth_vs_usual",
    "price_sensitivity_match",
]

# LightGBM hyperparameters
LGBM_PARAMS = {
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 50,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "class_weight": "balanced",
    "random_state": SEED,
    "verbose": -1,
}

# ---------------------------------------------------------------------------
# Drift monitoring
# ---------------------------------------------------------------------------
PSI_WARN_THRESHOLD = 0.10
PSI_ALERT_THRESHOLD = 0.25
DRIFT_RETRAIN_MIN_FEATURES = 3
DRIFT_FEATURES = [
    "recency_days",
    "frequency",
    "monetary",
    "promo_affinity",
    "avg_basket_size",
    "avg_discount_depth",
]

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
API_HOST = "0.0.0.0"
API_PORT = 8000

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = "INFO"
LOG_FORMAT = "json"
