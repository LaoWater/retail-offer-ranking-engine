"""
Test fixtures for Metro Romania Recommender.

Creates a small fixture database (100 customers, 50 products, 10 offers)
that all tests can share. Runs the mini data generation once per session.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import DATA_DIR, MODELS_DIR
from src.db import get_connection, init_db
from src.generate_data import MetroDataGenerator


TEST_DB_PATH = DATA_DIR / "test_metro.db"
TEST_RUN_DATE = "2026-02-01"


@pytest.fixture(scope="session")
def test_db():
    """
    Create a small test database once per test session.

    Generates: 100 customers, 50 products, 10 offers, ~2K order items,
    ~500 impressions, ~25 redemptions.
    """
    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    generator = MetroDataGenerator(
        seed=42,
        n_customers=100,
        n_products=50,
        n_offers=10,
        n_stores=5,
        history_days=90,
        target_order_items=2000,
        target_impressions=500,
    )
    generator.generate_all(db_path=TEST_DB_PATH)

    conn = get_connection(TEST_DB_PATH)
    yield conn
    conn.close()

    if TEST_DB_PATH.exists():
        os.remove(TEST_DB_PATH)


@pytest.fixture
def conn(test_db):
    """Provide the shared test connection."""
    return test_db


@pytest.fixture
def run_date():
    """Standard test run date."""
    return TEST_RUN_DATE
