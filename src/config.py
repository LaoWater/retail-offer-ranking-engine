"""
Configuration for Metro Romania Personalized Offers Recommender.
Single source of truth for all paths, hyperparameters, and constants.

Metro is a B2B cash-and-carry wholesaler. Every customer is a registered
business (HoReCa, Trader, SCO, Freelancer). All prices in RON.
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

# ---------------------------------------------------------------------------
# Purchase mode — dual-mode checkout
# Metro card holders choose at checkout: "business" or "individual" (personal)
# ~85-90% of orders are business purchases, ~10-15% are individual/personal
# (e.g., buying groceries for their own family using the Metro card)
# ---------------------------------------------------------------------------
PURCHASE_MODE_DIST = {
    "business": 0.87,
    "individual": 0.13,
}

# Individual purchase behavior differs from business:
# - Smaller basket sizes (household quantities, not wholesale)
# - Almost always tier 1 pricing (single units)
# - Higher fresh food ratio (buying for family meals)
# - Different category mix (more consumer-oriented)
INDIVIDUAL_PURCHASE_PROFILE = {
    "basket_size_multiplier": 0.20,       # ~20% of business basket size
    "tier2_probability": 0.05,            # rarely buy in case quantities
    "tier3_probability": 0.01,            # almost never buy bulk as individual
    "fresh_ratio_boost": 1.3,             # more fresh food for family
    "quantity_range": (1, 3),             # household quantities
}

# ---------------------------------------------------------------------------
# Business type distribution (B2B only — no consumers)
# ---------------------------------------------------------------------------
BUSINESS_TYPE_DIST = {
    "horeca": 0.50,
    "trader": 0.30,
    "sco": 0.12,
    "freelancer": 0.08,
}

BUSINESS_SUBTYPE_DIST = {
    "horeca": {
        "restaurant": 0.35,
        "cafe_bar": 0.20,
        "hotel": 0.10,
        "catering": 0.12,
        "fast_food": 0.10,
        "bakery_pastry": 0.08,
        "ghost_kitchen": 0.05,
    },
    "trader": {
        "grocery_store": 0.45,
        "convenience": 0.20,
        "specialty_food": 0.15,
        "liquor_store": 0.10,
        "general_retail": 0.10,
    },
    "sco": {
        "office": 0.35,
        "hospital_clinic": 0.20,
        "school_university": 0.20,
        "canteen": 0.15,
        "other_org": 0.10,
    },
    "freelancer": {
        "independent_pro": 0.50,
        "small_business": 0.50,
    },
}

# Loyalty tier distribution by business type (classic/plus/star)
LOYALTY_TIERS = {
    "horeca":     {"classic": 0.30, "plus": 0.45, "star": 0.25},
    "trader":     {"classic": 0.50, "plus": 0.35, "star": 0.15},
    "sco":        {"classic": 0.40, "plus": 0.40, "star": 0.20},
    "freelancer": {"classic": 0.70, "plus": 0.25, "star": 0.05},
}

# ---------------------------------------------------------------------------
# Business behavioral profiles (per subtype)
# ---------------------------------------------------------------------------
BUSINESS_PROFILES = {
    # HoReCa subtypes
    "restaurant": {
        "purchase_freq_weekly": 3.5,
        "basket_size_mean": 45,
        "basket_size_std": 15,
        "promo_affinity": 0.25,
        "price_sensitivity": 0.45,
        "fresh_ratio": 0.65,
        "email_consent_rate": 0.70,
        "sms_consent_rate": 0.55,
        "app_registered_rate": 0.40,
    },
    "cafe_bar": {
        "purchase_freq_weekly": 3.0,
        "basket_size_mean": 30,
        "basket_size_std": 10,
        "promo_affinity": 0.30,
        "price_sensitivity": 0.50,
        "fresh_ratio": 0.45,
        "email_consent_rate": 0.65,
        "sms_consent_rate": 0.50,
        "app_registered_rate": 0.35,
    },
    "hotel": {
        "purchase_freq_weekly": 4.0,
        "basket_size_mean": 60,
        "basket_size_std": 20,
        "promo_affinity": 0.15,
        "price_sensitivity": 0.30,
        "fresh_ratio": 0.55,
        "email_consent_rate": 0.80,
        "sms_consent_rate": 0.40,
        "app_registered_rate": 0.50,
    },
    "catering": {
        "purchase_freq_weekly": 2.5,
        "basket_size_mean": 70,
        "basket_size_std": 25,
        "promo_affinity": 0.35,
        "price_sensitivity": 0.55,
        "fresh_ratio": 0.60,
        "email_consent_rate": 0.75,
        "sms_consent_rate": 0.45,
        "app_registered_rate": 0.30,
    },
    "fast_food": {
        "purchase_freq_weekly": 4.0,
        "basket_size_mean": 35,
        "basket_size_std": 12,
        "promo_affinity": 0.40,
        "price_sensitivity": 0.60,
        "fresh_ratio": 0.40,
        "email_consent_rate": 0.60,
        "sms_consent_rate": 0.55,
        "app_registered_rate": 0.45,
    },
    "bakery_pastry": {
        "purchase_freq_weekly": 5.0,
        "basket_size_mean": 25,
        "basket_size_std": 8,
        "promo_affinity": 0.20,
        "price_sensitivity": 0.40,
        "fresh_ratio": 0.70,
        "email_consent_rate": 0.55,
        "sms_consent_rate": 0.45,
        "app_registered_rate": 0.25,
    },
    "ghost_kitchen": {
        "purchase_freq_weekly": 4.5,
        "basket_size_mean": 40,
        "basket_size_std": 15,
        "promo_affinity": 0.35,
        "price_sensitivity": 0.55,
        "fresh_ratio": 0.50,
        "email_consent_rate": 0.80,
        "sms_consent_rate": 0.60,
        "app_registered_rate": 0.70,
    },
    # Trader subtypes
    "grocery_store": {
        "purchase_freq_weekly": 2.0,
        "basket_size_mean": 55,
        "basket_size_std": 20,
        "promo_affinity": 0.55,
        "price_sensitivity": 0.75,
        "fresh_ratio": 0.35,
        "email_consent_rate": 0.50,
        "sms_consent_rate": 0.60,
        "app_registered_rate": 0.20,
    },
    "convenience": {
        "purchase_freq_weekly": 2.5,
        "basket_size_mean": 40,
        "basket_size_std": 15,
        "promo_affinity": 0.50,
        "price_sensitivity": 0.70,
        "fresh_ratio": 0.30,
        "email_consent_rate": 0.45,
        "sms_consent_rate": 0.55,
        "app_registered_rate": 0.25,
    },
    "specialty_food": {
        "purchase_freq_weekly": 1.5,
        "basket_size_mean": 35,
        "basket_size_std": 12,
        "promo_affinity": 0.30,
        "price_sensitivity": 0.50,
        "fresh_ratio": 0.45,
        "email_consent_rate": 0.60,
        "sms_consent_rate": 0.40,
        "app_registered_rate": 0.30,
    },
    "liquor_store": {
        "purchase_freq_weekly": 1.5,
        "basket_size_mean": 30,
        "basket_size_std": 10,
        "promo_affinity": 0.45,
        "price_sensitivity": 0.65,
        "fresh_ratio": 0.05,
        "email_consent_rate": 0.40,
        "sms_consent_rate": 0.50,
        "app_registered_rate": 0.15,
    },
    "general_retail": {
        "purchase_freq_weekly": 1.0,
        "basket_size_mean": 45,
        "basket_size_std": 18,
        "promo_affinity": 0.50,
        "price_sensitivity": 0.70,
        "fresh_ratio": 0.20,
        "email_consent_rate": 0.45,
        "sms_consent_rate": 0.50,
        "app_registered_rate": 0.20,
    },
    # SCO subtypes
    "office": {
        "purchase_freq_weekly": 0.8,
        "basket_size_mean": 25,
        "basket_size_std": 10,
        "promo_affinity": 0.20,
        "price_sensitivity": 0.40,
        "fresh_ratio": 0.10,
        "email_consent_rate": 0.70,
        "sms_consent_rate": 0.30,
        "app_registered_rate": 0.40,
    },
    "hospital_clinic": {
        "purchase_freq_weekly": 1.5,
        "basket_size_mean": 40,
        "basket_size_std": 15,
        "promo_affinity": 0.15,
        "price_sensitivity": 0.30,
        "fresh_ratio": 0.25,
        "email_consent_rate": 0.65,
        "sms_consent_rate": 0.25,
        "app_registered_rate": 0.35,
    },
    "school_university": {
        "purchase_freq_weekly": 1.0,
        "basket_size_mean": 50,
        "basket_size_std": 20,
        "promo_affinity": 0.25,
        "price_sensitivity": 0.55,
        "fresh_ratio": 0.30,
        "email_consent_rate": 0.60,
        "sms_consent_rate": 0.30,
        "app_registered_rate": 0.30,
    },
    "canteen": {
        "purchase_freq_weekly": 3.0,
        "basket_size_mean": 55,
        "basket_size_std": 18,
        "promo_affinity": 0.30,
        "price_sensitivity": 0.50,
        "fresh_ratio": 0.55,
        "email_consent_rate": 0.55,
        "sms_consent_rate": 0.35,
        "app_registered_rate": 0.25,
    },
    "other_org": {
        "purchase_freq_weekly": 0.5,
        "basket_size_mean": 20,
        "basket_size_std": 8,
        "promo_affinity": 0.20,
        "price_sensitivity": 0.45,
        "fresh_ratio": 0.15,
        "email_consent_rate": 0.50,
        "sms_consent_rate": 0.25,
        "app_registered_rate": 0.20,
    },
    # Freelancer subtypes
    "independent_pro": {
        "purchase_freq_weekly": 0.5,
        "basket_size_mean": 12,
        "basket_size_std": 5,
        "promo_affinity": 0.40,
        "price_sensitivity": 0.60,
        "fresh_ratio": 0.20,
        "email_consent_rate": 0.55,
        "sms_consent_rate": 0.40,
        "app_registered_rate": 0.45,
    },
    "small_business": {
        "purchase_freq_weekly": 0.8,
        "basket_size_mean": 18,
        "basket_size_std": 7,
        "promo_affinity": 0.45,
        "price_sensitivity": 0.65,
        "fresh_ratio": 0.15,
        "email_consent_rate": 0.60,
        "sms_consent_rate": 0.45,
        "app_registered_rate": 0.40,
    },
}

# ---------------------------------------------------------------------------
# Product categories (21 categories: 13 food ~90%, 8 non-food ~10%)
# Fish/seafood and meat are Metro Romania's flagship departments
# ---------------------------------------------------------------------------
CATEGORIES = [
    # Food (~90% of assortment — Metro is overwhelmingly food-focused)
    # Fish/seafood and meat are Metro Romania's signature categories
    ("meat_poultry", 0.14),              # Metro's butchery is a flagship department
    ("seafood", 0.10),                   # Fish is #1 in Metro's app — sushi restaurants rely on Metro imports
    ("dairy_eggs", 0.10),
    ("fruits_vegetables", 0.10),
    ("beverages_non_alcoholic", 0.08),
    ("bakery_pastry", 0.07),
    ("frozen_foods", 0.06),
    ("grocery_staples", 0.06),
    ("beverages_alcoholic", 0.06),
    ("confectionery_snacks", 0.04),
    ("deli_charcuterie", 0.04),
    ("condiments_spices", 0.03),
    ("coffee_tea", 0.03),
    # Non-Food (~10% — "first line" assortment, not deep)
    ("cleaning_detergents", 0.02),
    ("kitchen_utensils_tableware", 0.02),
    ("horeca_equipment", 0.015),
    ("paper_packaging", 0.015),
    ("personal_care_hygiene", 0.01),
    ("household_goods", 0.005),
    ("office_supplies", 0.005),
    ("electronics_small_appliances", 0.005),
]  # Weights sum to ~1.0 (normalized at runtime)

CATEGORY_NAMES = [c[0] for c in CATEGORIES]
CATEGORY_WEIGHTS = [c[1] for c in CATEGORIES]

# Fresh categories (perishable)
FRESH_CATEGORIES = {
    "meat_poultry", "dairy_eggs", "fruits_vegetables",
    "bakery_pastry", "seafood", "deli_charcuterie",
}

# Subcategories per category (Romanian-specific items)
SUBCATEGORIES = {
    "meat_poultry": ["beef", "pork", "chicken", "lamb", "sausages", "mici", "costita", "ceafa"],
    "dairy_eggs": ["milk", "cheese_telemea", "cheese_cascaval", "branza", "yogurt", "butter", "cream", "eggs", "smantana"],
    "fruits_vegetables": ["fruits", "vegetables", "herbs", "salads", "potatoes", "onions", "root_vegetables"],
    "beverages_non_alcoholic": ["water", "juice", "soft_drinks", "energy_drinks", "mineral_water"],
    "bakery_pastry": ["bread", "rolls", "pastries", "covrigi", "frozen_prebaked", "paine_alba", "paine_integrala"],
    "frozen_foods": ["frozen_vegetables", "frozen_meals", "ice_cream", "frozen_proteins", "frozen_pizza"],
    "grocery_staples": ["rice", "pasta", "flour", "sunflower_oil", "sugar", "polenta_mamaliga", "canned_goods", "conserve"],
    "beverages_alcoholic": ["beer", "wine", "spirits_tuica", "spirits_palinca", "vodka", "whisky"],
    "seafood": ["crap", "pastrav", "salmon", "shrimp", "preserved_fish", "sushi_grade", "cod", "tuna", "calamari", "sardines", "mackerel"],
    "confectionery_snacks": ["chocolate", "candy", "chips", "crackers", "nuts", "biscuits"],
    "condiments_spices": ["ketchup", "mustard", "mayo", "sauces", "spices", "bors_liquid"],
    "deli_charcuterie": ["ham", "salami_sibiu", "slanina", "olives", "muraturi", "sunca_praga"],
    "coffee_tea": ["ground_coffee", "whole_bean", "pods", "instant", "tea"],
    "cleaning_detergents": ["industrial_cleaning", "dishwashing", "laundry", "disinfectants", "floor_care"],
    "kitchen_utensils_tableware": ["pots_pans", "knives", "cutting_boards", "plates", "glasses", "serving"],
    "horeca_equipment": ["commercial_ovens", "refrigerators", "display_cases", "buffet_systems", "prep_equipment"],
    "paper_packaging": ["napkins", "takeaway_containers", "foil", "cling_wrap", "bags", "cups"],
    "personal_care_hygiene": ["soap", "shampoo", "dental", "skincare", "hand_sanitizer"],
    "household_goods": ["storage", "textiles_aprons", "work_clothing", "table_linens"],
    "office_supplies": ["paper", "stationery", "printer_supplies", "filing"],
    "electronics_small_appliances": ["small_electronics", "calculators", "pos_accessories", "lighting"],
}

# Base price ranges by category (RON, wholesale quantities)
CATEGORY_PRICE_RANGE = {
    "meat_poultry": (15.0, 120.0),
    "dairy_eggs": (4.0, 80.0),
    "fruits_vegetables": (3.0, 40.0),
    "beverages_non_alcoholic": (2.5, 35.0),
    "bakery_pastry": (3.0, 25.0),
    "frozen_foods": (8.0, 60.0),
    "grocery_staples": (5.0, 45.0),
    "beverages_alcoholic": (8.0, 200.0),
    "seafood": (20.0, 150.0),
    "confectionery_snacks": (4.0, 30.0),
    "condiments_spices": (4.0, 30.0),
    "deli_charcuterie": (10.0, 60.0),
    "coffee_tea": (15.0, 80.0),
    "cleaning_detergents": (5.0, 75.0),
    "kitchen_utensils_tableware": (10.0, 200.0),
    "horeca_equipment": (200.0, 5000.0),
    "paper_packaging": (5.0, 50.0),
    "personal_care_hygiene": (5.0, 60.0),
    "household_goods": (10.0, 150.0),
    "office_supplies": (5.0, 80.0),
    "electronics_small_appliances": (30.0, 500.0),
}

# Margin ranges by category (fraction)
CATEGORY_MARGIN_RANGE = {
    "meat_poultry": (0.06, 0.18),
    "dairy_eggs": (0.08, 0.20),
    "fruits_vegetables": (0.10, 0.30),
    "beverages_non_alcoholic": (0.12, 0.35),
    "bakery_pastry": (0.15, 0.40),
    "frozen_foods": (0.10, 0.25),
    "grocery_staples": (0.05, 0.15),
    "beverages_alcoholic": (0.15, 0.40),
    "seafood": (0.06, 0.15),
    "confectionery_snacks": (0.15, 0.40),
    "condiments_spices": (0.12, 0.30),
    "deli_charcuterie": (0.10, 0.25),
    "coffee_tea": (0.15, 0.35),
    "cleaning_detergents": (0.12, 0.30),
    "kitchen_utensils_tableware": (0.15, 0.35),
    "horeca_equipment": (0.20, 0.45),
    "paper_packaging": (0.12, 0.28),
    "personal_care_hygiene": (0.15, 0.35),
    "household_goods": (0.12, 0.30),
    "office_supplies": (0.10, 0.25),
    "electronics_small_appliances": (0.15, 0.35),
}

# Shelf life by category (days)
CATEGORY_SHELF_LIFE = {
    "meat_poultry": (3, 10),
    "dairy_eggs": (7, 30),
    "fruits_vegetables": (3, 14),
    "beverages_non_alcoholic": (90, 365),
    "bakery_pastry": (2, 7),
    "frozen_foods": (90, 365),
    "grocery_staples": (90, 365),
    "beverages_alcoholic": (365, 3650),
    "seafood": (2, 7),
    "confectionery_snacks": (60, 365),
    "condiments_spices": (180, 730),
    "deli_charcuterie": (5, 14),
    "coffee_tea": (180, 730),
    "cleaning_detergents": (365, 1095),
    "kitchen_utensils_tableware": (365, 3650),
    "horeca_equipment": (365, 3650),
    "paper_packaging": (365, 1095),
    "personal_care_hygiene": (180, 730),
    "household_goods": (365, 1095),
    "office_supplies": (365, 1095),
    "electronics_small_appliances": (365, 1825),
}

# ---------------------------------------------------------------------------
# Tiered pricing ("Staffelpreise") — Metro's signature pricing model
# ---------------------------------------------------------------------------
TIER_DISCOUNT_RANGES = {
    "tier2_discount": (0.05, 0.15),   # 5-15% off tier1
    "tier3_discount": (0.15, 0.35),   # 15-35% off tier1
}

# Default tier quantity thresholds by category
TIER_QUANTITY_THRESHOLDS = {
    "meat_poultry":               {"tier2_qty": 3, "tier3_qty": 10},
    "dairy_eggs":                 {"tier2_qty": 6, "tier3_qty": 24},
    "fruits_vegetables":          {"tier2_qty": 5, "tier3_qty": 20},
    "beverages_non_alcoholic":    {"tier2_qty": 6, "tier3_qty": 24},
    "bakery_pastry":              {"tier2_qty": 6, "tier3_qty": 20},
    "frozen_foods":               {"tier2_qty": 4, "tier3_qty": 12},
    "grocery_staples":            {"tier2_qty": 5, "tier3_qty": 20},
    "beverages_alcoholic":        {"tier2_qty": 6, "tier3_qty": 24},
    "seafood":                    {"tier2_qty": 3, "tier3_qty": 10},
    "confectionery_snacks":       {"tier2_qty": 6, "tier3_qty": 24},
    "condiments_spices":          {"tier2_qty": 6, "tier3_qty": 20},
    "deli_charcuterie":           {"tier2_qty": 3, "tier3_qty": 10},
    "coffee_tea":                 {"tier2_qty": 6, "tier3_qty": 24},
    "cleaning_detergents":        {"tier2_qty": 4, "tier3_qty": 12},
    "kitchen_utensils_tableware": {"tier2_qty": 3, "tier3_qty": 10},
    "horeca_equipment":           {"tier2_qty": 2, "tier3_qty": 5},
    "paper_packaging":            {"tier2_qty": 5, "tier3_qty": 20},
    "personal_care_hygiene":      {"tier2_qty": 6, "tier3_qty": 24},
    "household_goods":            {"tier2_qty": 3, "tier3_qty": 10},
    "office_supplies":            {"tier2_qty": 5, "tier3_qty": 20},
    "electronics_small_appliances": {"tier2_qty": 2, "tier3_qty": 5},
}

# ---------------------------------------------------------------------------
# Metro own brands
# ---------------------------------------------------------------------------
METRO_OWN_BRANDS = {
    "metro_chef": {
        "categories": [
            "meat_poultry", "dairy_eggs", "fruits_vegetables", "frozen_foods",
            "grocery_staples", "seafood", "bakery_pastry", "condiments_spices",
            "deli_charcuterie",
        ],
        "price_factor": 0.85,
        "margin_factor": 1.40,
    },
    "metro_premium": {
        "categories": [
            "meat_poultry", "dairy_eggs", "seafood", "deli_charcuterie",
            "beverages_alcoholic", "coffee_tea",
        ],
        "price_factor": 0.95,
        "margin_factor": 1.30,
    },
    "metro_professional": {
        "categories": [
            "kitchen_utensils_tableware", "horeca_equipment", "household_goods",
            "paper_packaging", "cleaning_detergents",
        ],
        "price_factor": 0.88,
        "margin_factor": 1.35,
    },
    "aro": {
        "categories": [
            "dairy_eggs", "frozen_foods", "grocery_staples", "beverages_non_alcoholic",
            "confectionery_snacks", "cleaning_detergents", "paper_packaging",
            "personal_care_hygiene",
        ],
        "price_factor": 0.65,
        "margin_factor": 1.30,
    },
    "rioba": {
        "categories": ["coffee_tea", "beverages_non_alcoholic"],
        "price_factor": 0.82,
        "margin_factor": 1.35,
    },
    "horeca_select": {
        "categories": [
            "meat_poultry", "dairy_eggs", "frozen_foods", "seafood",
            "condiments_spices", "grocery_staples",
        ],
        "price_factor": 0.80,
        "margin_factor": 1.40,
    },
    "tarrington_house": {
        "categories": ["household_goods", "kitchen_utensils_tableware"],
        "price_factor": 0.82,
        "margin_factor": 1.30,
    },
    "h_line": {
        "categories": ["paper_packaging", "cleaning_detergents"],
        "price_factor": 0.78,
        "margin_factor": 1.35,
    },
    "sigma": {
        "categories": ["office_supplies", "electronics_small_appliances"],
        "price_factor": 0.80,
        "margin_factor": 1.30,
    },
}

OWN_BRAND_PROBABILITY = 0.30

# ---------------------------------------------------------------------------
# Romanian brands per category
# ---------------------------------------------------------------------------
ROMANIAN_BRANDS = {
    "beverages_non_alcoholic": ["Borsec", "Dorna", "Bucovina", "Aqua Carpatica", "Olympus"],
    "beverages_alcoholic": ["Ursus", "Timisoreana", "Silva", "Jidvei", "Cotnari", "Alexandrion", "Zetea"],
    "confectionery_snacks": ["ROM", "Joe", "Heidi", "Kandia", "Guylian"],
    "dairy_eggs": ["Albalact", "Zuzu", "Napolact", "Covalact", "LaDorna"],
    "meat_poultry": ["Agricola", "Caroli", "CrisTim", "Meda", "Angst"],
    "bakery_pastry": ["Vel Pitar", "Dobrogea", "Panifcom"],
    "grocery_staples": ["Bunge", "Untdelemn de la Bunica", "Pambac"],
    "condiments_spices": ["Raureni", "Olympia", "Bunica"],
    "deli_charcuterie": ["Cris-Tim", "Angst", "Caroli", "Sergiana"],
}

BRANDS_PER_CATEGORY = 8

# ---------------------------------------------------------------------------
# Category affinity multipliers by business subtype
# ---------------------------------------------------------------------------
BUSINESS_CATEGORY_AFFINITY = {
    "restaurant": {
        "meat_poultry": 3.0, "dairy_eggs": 2.0, "fruits_vegetables": 2.5,
        "condiments_spices": 2.0, "seafood": 2.0, "beverages_alcoholic": 1.8,
        "grocery_staples": 1.5, "deli_charcuterie": 1.5,
        "office_supplies": 0.1, "electronics_small_appliances": 0.1,
    },
    "cafe_bar": {
        "coffee_tea": 4.0, "beverages_alcoholic": 3.0, "beverages_non_alcoholic": 2.5,
        "confectionery_snacks": 2.0, "bakery_pastry": 2.0, "dairy_eggs": 1.5,
        "meat_poultry": 0.5, "office_supplies": 0.1, "horeca_equipment": 0.3,
    },
    "hotel": {
        "cleaning_detergents": 2.5, "personal_care_hygiene": 3.0,
        "household_goods": 2.0, "beverages_non_alcoholic": 1.8,
        "beverages_alcoholic": 1.5, "coffee_tea": 2.0,
        "paper_packaging": 1.5, "meat_poultry": 1.5, "dairy_eggs": 1.5,
    },
    "catering": {
        "meat_poultry": 3.0, "dairy_eggs": 2.5, "fruits_vegetables": 2.5,
        "frozen_foods": 2.0, "paper_packaging": 2.5, "grocery_staples": 2.0,
        "condiments_spices": 1.8, "cleaning_detergents": 1.5,
        "office_supplies": 0.1, "electronics_small_appliances": 0.1,
    },
    "fast_food": {
        "frozen_foods": 3.0, "meat_poultry": 2.5, "beverages_non_alcoholic": 2.5,
        "paper_packaging": 3.0, "grocery_staples": 2.0, "condiments_spices": 2.5,
        "seafood": 0.3, "beverages_alcoholic": 0.3,
    },
    "bakery_pastry": {
        "dairy_eggs": 3.5, "grocery_staples": 3.0, "bakery_pastry": 2.0,
        "confectionery_snacks": 2.0, "fruits_vegetables": 1.5,
        "meat_poultry": 0.3, "seafood": 0.2,
    },
    "ghost_kitchen": {
        "meat_poultry": 2.5, "frozen_foods": 2.0, "paper_packaging": 3.0,
        "grocery_staples": 2.0, "condiments_spices": 2.0,
        "beverages_non_alcoholic": 2.0, "cleaning_detergents": 1.5,
    },
    "grocery_store": {
        "grocery_staples": 2.5, "beverages_non_alcoholic": 2.0,
        "confectionery_snacks": 2.0, "dairy_eggs": 1.8,
        "cleaning_detergents": 1.5, "personal_care_hygiene": 1.5,
        "beverages_alcoholic": 1.5, "frozen_foods": 1.5,
        "horeca_equipment": 0.1,
    },
    "convenience": {
        "beverages_non_alcoholic": 2.5, "confectionery_snacks": 2.5,
        "beverages_alcoholic": 2.0, "grocery_staples": 1.5,
        "dairy_eggs": 1.5, "bakery_pastry": 1.5,
        "horeca_equipment": 0.1, "seafood": 0.3,
    },
    "specialty_food": {
        "deli_charcuterie": 3.0, "dairy_eggs": 2.5, "beverages_alcoholic": 2.5,
        "confectionery_snacks": 2.0, "coffee_tea": 2.0, "condiments_spices": 1.8,
        "cleaning_detergents": 0.3, "office_supplies": 0.1,
    },
    "liquor_store": {
        "beverages_alcoholic": 5.0, "beverages_non_alcoholic": 2.0,
        "confectionery_snacks": 1.5, "coffee_tea": 1.0,
        "meat_poultry": 0.1, "dairy_eggs": 0.1, "fruits_vegetables": 0.1,
    },
    "general_retail": {
        "household_goods": 2.0, "cleaning_detergents": 2.0,
        "personal_care_hygiene": 2.0, "grocery_staples": 1.5,
        "confectionery_snacks": 1.5, "beverages_non_alcoholic": 1.5,
    },
    "office": {
        "office_supplies": 5.0, "paper_packaging": 2.0, "coffee_tea": 2.5,
        "beverages_non_alcoholic": 2.0, "cleaning_detergents": 1.5,
        "confectionery_snacks": 1.5,
        "meat_poultry": 0.1, "seafood": 0.1,
    },
    "hospital_clinic": {
        "cleaning_detergents": 3.0, "personal_care_hygiene": 3.0,
        "paper_packaging": 2.5, "beverages_non_alcoholic": 1.5,
        "office_supplies": 1.5, "household_goods": 1.5,
        "beverages_alcoholic": 0.1,
    },
    "school_university": {
        "office_supplies": 2.5, "cleaning_detergents": 2.0,
        "beverages_non_alcoholic": 2.0, "confectionery_snacks": 1.5,
        "paper_packaging": 2.0, "grocery_staples": 1.5,
        "beverages_alcoholic": 0.1,
    },
    "canteen": {
        "meat_poultry": 2.5, "dairy_eggs": 2.0, "fruits_vegetables": 2.0,
        "frozen_foods": 2.0, "grocery_staples": 2.5, "cleaning_detergents": 1.5,
        "paper_packaging": 1.5, "condiments_spices": 1.5,
    },
    "other_org": {
        "office_supplies": 2.0, "cleaning_detergents": 1.5,
        "beverages_non_alcoholic": 1.5, "paper_packaging": 1.5,
        "coffee_tea": 1.5,
    },
    "independent_pro": {
        "office_supplies": 2.0, "coffee_tea": 2.0, "confectionery_snacks": 1.5,
        "beverages_non_alcoholic": 1.5, "cleaning_detergents": 1.0,
    },
    "small_business": {
        "office_supplies": 2.5, "cleaning_detergents": 1.5,
        "beverages_non_alcoholic": 1.5, "paper_packaging": 1.5,
        "coffee_tea": 1.5, "personal_care_hygiene": 1.0,
    },
}

# ---------------------------------------------------------------------------
# Seasonal multipliers (day_of_year -> multiplier)
# ---------------------------------------------------------------------------
SEASONAL_EVENTS = {
    "christmas": {"start_day": 344, "end_day": 358, "multiplier": 2.5},
    "easter": {"start_day": 91, "end_day": 105, "multiplier": 1.8},
    "summer_bbq": {"start_day": 182, "end_day": 243, "multiplier": 1.3},
    "new_year": {"start_day": 1, "end_day": 5, "multiplier": 1.5},
}

# Weekly purchase patterns (day_of_week -> multiplier)
# HoReCa customers peak Mon/Thu (restocking), traders peak Tue/Wed
WEEKLY_PATTERNS = {
    "horeca": {0: 1.4, 1: 1.0, 2: 1.0, 3: 1.3, 4: 0.9, 5: 0.7, 6: 0.3},
    "trader":  {0: 0.9, 1: 1.2, 2: 1.3, 3: 1.0, 4: 1.0, 5: 0.8, 6: 0.3},
    "sco":     {0: 1.1, 1: 1.1, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.5, 6: 0.1},
    "freelancer": {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.2, 5: 1.0, 6: 0.5},
}

# ---------------------------------------------------------------------------
# Offer types and campaign config
# ---------------------------------------------------------------------------
OFFER_TYPE_DIST = {
    "percentage": 0.35,
    "fixed_amount": 0.20,
    "buy_x_get_y": 0.15,
    "volume_bonus": 0.15,
    "bundle": 0.10,
    "free_gift": 0.05,
}

CAMPAIGN_TYPE_DIST = {
    "weekly_catalog": 0.35,
    "personalized": 0.25,
    "seasonal": 0.15,
    "churn_prevention": 0.08,
    "reactivation": 0.05,
    "new_customer": 0.04,
    "birthday": 0.03,
    "cross_sell": 0.05,
}

CHANNEL_DIST = {
    "email": 0.30,
    "app": 0.25,
    "catalog": 0.20,
    "sms": 0.15,
    "in_store": 0.10,
}

# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------
CANDIDATE_POOL_SIZE = 200
CANDIDATE_STRATEGY_LIMITS = {
    "category_affinity": 60,
    "business_type_popular": 40,
    "repeat_purchase": 30,
    "high_margin": 20,
    "tier_upgrade": 20,
    "cross_sell": 15,
    "own_brand_switch": 15,
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
    # Customer features (RFM + behavior)
    "recency_days",
    "frequency",
    "monetary",
    "promo_affinity",
    "avg_basket_size",
    "category_entropy",
    "avg_discount_depth",
    "avg_basket_quantity",
    "tier2_purchase_ratio",
    "tier3_purchase_ratio",
    "fresh_category_ratio",
    "business_order_ratio",
    # Segment identity — ordinal encoded (horeca=0, trader=1, sco=2, freelancer=3)
    "business_type_encoded",
    # Offer features
    "discount_depth",
    "margin_impact",
    "days_until_expiry",
    "historical_redemption_rate",
    "is_own_brand",
    # Interaction features
    "bought_product_before",
    "days_since_last_cat_purchase",
    "category_affinity_score",
    "discount_depth_vs_usual",
    "price_sensitivity_match",
    "business_type_match",
]

# Ordinal encoding for business_type (used in train_ranker + score_ranker)
BUSINESS_TYPE_ENCODING = {
    "horeca": 0,
    "trader": 1,
    "sco": 2,
    "freelancer": 3,
}

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
    "tier2_purchase_ratio",
    "tier3_purchase_ratio",
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
