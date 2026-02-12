"""Tests for the FastAPI service."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from src.api import app, get_db
from src.config import DATA_DIR
from src.db import get_connection

TEST_DB_PATH = DATA_DIR / "test_metro.db"


def override_get_db():
    """Override DB dependency to use test database."""
    conn = get_connection(TEST_DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealthEndpoint:
    def test_returns_200(self):
        if not TEST_DB_PATH.exists():
            pytest.skip("Test DB not generated yet")
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_schema(self):
        if not TEST_DB_PATH.exists():
            pytest.skip("Test DB not generated yet")
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "db_size_mb" in data
        assert "total_customers" in data


class TestRecommendationsEndpoint:
    def test_invalid_customer_returns_404(self):
        if not TEST_DB_PATH.exists():
            pytest.skip("Test DB not generated yet")
        response = client.get("/recommendations?customer_id=999999")
        assert response.status_code == 404

    def test_missing_customer_id_returns_422(self):
        if not TEST_DB_PATH.exists():
            pytest.skip("Test DB not generated yet")
        response = client.get("/recommendations")
        assert response.status_code == 422


class TestCustomerEndpoint:
    def test_valid_customer(self):
        if not TEST_DB_PATH.exists():
            pytest.skip("Test DB not generated yet")
        response = client.get("/customers/1")
        # Either 200 (found) or 404 (not in test DB)
        assert response.status_code in (200, 404)

    def test_invalid_customer(self):
        if not TEST_DB_PATH.exists():
            pytest.skip("Test DB not generated yet")
        response = client.get("/customers/999999")
        assert response.status_code == 404


class TestBatchEndpoint:
    def test_empty_ids_returns_400(self):
        if not TEST_DB_PATH.exists():
            pytest.skip("Test DB not generated yet")
        response = client.get("/recommendations/batch?customer_ids=")
        assert response.status_code == 400
