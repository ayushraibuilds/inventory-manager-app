"""Unit tests for API routes using FastAPI TestClient with mocked Supabase."""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock environment variables before importing the app
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ["API_KEY"] = "test-api-key"  # Set a known key for authenticated endpoints

from tests.conftest import MockSupabaseClient


# We need to patch the Supabase client before importing the app
_mock_data = {
    "profiles": [{"id": "test-seller", "user_id": "test-seller", "store_name": "Test Store", "phone": "+1234567890", "low_stock_alerts": False}],
    "products": [],
    "activity_log": [],
    "orders": [],
}
_mock_client = MockSupabaseClient(data_map=_mock_data)


@pytest.fixture(autouse=True)
def patch_supabase():
    with patch("db.get_supabase_client", return_value=_mock_client):
        yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from server import app
    return TestClient(app, headers={"X-API-Key": "test-api-key"})


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        # Patch the LLM check in health to avoid real API call
        with patch("langchain_groq.ChatGroq") as mock_groq:
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = "pong"
            mock_groq.return_value = mock_llm
            response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "supabase" in data
        assert "llm" in data


class TestCatalogEndpoints:
    def test_get_catalog_returns_200(self, client):
        response = client.get("/api/catalog")
        assert response.status_code == 200
        data = response.json()
        assert "bpp/catalog" in data
        assert "pagination" in data

    def test_get_catalog_with_seller_id(self, client):
        response = client.get("/api/catalog?seller_id=test-seller")
        assert response.status_code == 200

    def test_get_catalog_with_search(self, client):
        response = client.get("/api/catalog?search=atta")
        assert response.status_code == 200

    def test_create_item_returns_success(self, client):
        response = client.post(
            "/api/catalog/item",
            json={
                "name": "Test Atta",
                "price": "450",
                "quantity": 10,
                "unit": "kg",
                "seller_id": "test-seller",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["item"]["descriptor"]["name"] == "Test Atta"

    def test_create_item_rejects_negative_price(self, client):
        response = client.post(
            "/api/catalog/item",
            json={
                "name": "Bad Item",
                "price": "-10",
                "quantity": 5,
                "unit": "piece",
                "seller_id": "test-seller",
            },
        )
        assert response.status_code == 422  # Validation error

    def test_create_item_rejects_html_in_name(self, client):
        response = client.post(
            "/api/catalog/item",
            json={
                "name": "<script>alert(1)</script>Atta",
                "price": "100",
                "quantity": 5,
                "unit": "kg",
                "seller_id": "test-seller",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Name should be sanitized
        assert "<script>" not in data["item"]["descriptor"]["name"]

    def test_create_item_rejects_negative_quantity(self, client):
        response = client.post(
            "/api/catalog/item",
            json={
                "name": "Atta",
                "price": "100",
                "quantity": -5,
                "unit": "kg",
                "seller_id": "test-seller",
            },
        )
        assert response.status_code == 422


class TestSellersEndpoint:
    def test_list_sellers_returns_200(self, client):
        response = client.get("/api/sellers")
        assert response.status_code == 200
        data = response.json()
        assert "sellers" in data

    def test_get_profile_returns_200(self, client):
        response = client.get("/api/seller/test-seller/profile")
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data


class TestOrdersEndpoint:
    def test_list_orders_returns_200(self, client):
        response = client.get("/api/orders")
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data

    def test_create_order_returns_success(self, client):
        with patch("routes.orders.send_whatsapp_reply"):
            response = client.post(
                "/api/orders",
                json={
                    "seller_id": "test-seller",
                    "buyer_name": "Test Buyer",
                    "buyer_phone": "+1234567890",
                    "items": [{"name": "Atta", "quantity": 2}],
                    "total_amount": 900.0,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "order_id" in data


class TestActivityEndpoint:
    def test_activity_returns_200(self, client):
        response = client.get("/api/activity")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
