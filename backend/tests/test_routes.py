"""Unit tests for API routes using FastAPI TestClient with mocked Supabase."""
import sys
import os
import builtins
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
from billing import BillingError


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


@pytest.fixture
def client_no_auth():
    from fastapi.testclient import TestClient
    from server import app
    return TestClient(app)


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

    def test_get_catalog_requires_auth(self, client_no_auth):
        response = client_no_auth.get("/api/catalog?seller_id=test-seller")
        assert response.status_code == 401

    def test_get_catalog_search_happens_before_pagination(self, client):
        mock_catalog = {
            "bpp/catalog": {
                "bpp/providers": [
                    {
                        "items": [
                            {
                                "id": "1",
                                "descriptor": {"name": "Salt"},
                                "price": {"value": "10"},
                                "quantity": {"available": {"count": 5}},
                                "category_id": "Grocery",
                            },
                            {
                                "id": "2",
                                "descriptor": {"name": "Rice"},
                                "price": {"value": "50"},
                                "quantity": {"available": {"count": 3}},
                                "category_id": "Grocery",
                            },
                        ]
                    }
                ]
            }
        }
        with patch("routes.catalog.get_catalog", return_value=mock_catalog):
            response = client.get(
                "/api/catalog?seller_id=test-seller&search=rice&limit=1&offset=0"
            )
        assert response.status_code == 200
        items = response.json()["bpp/catalog"]["bpp/providers"][0]["items"]
        assert len(items) == 1
        assert items[0]["descriptor"]["name"] == "Rice"

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

    def test_create_item_blocks_when_plan_limit_hit(self, client):
        with patch(
            "routes.catalog.assert_product_limit_or_raise",
            side_effect=BillingError(
                "PRODUCT_LIMIT_EXCEEDED",
                "Free plan allows up to 100 products.",
                status_code=403,
            ),
        ):
            response = client.post(
                "/api/catalog/item",
                json={
                    "name": "Overflow Item",
                    "price": "250",
                    "quantity": 1,
                    "unit": "piece",
                    "seller_id": "test-seller",
                },
            )
        assert response.status_code == 403
        assert response.json()["detail"] == "Free plan allows up to 100 products."


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

    def test_update_profile_requires_auth(self, client_no_auth):
        response = client_no_auth.put(
            "/api/seller/test-seller/profile",
            json={"store_name": "Hijack Store"},
        )
        assert response.status_code == 401


class TestOrdersEndpoint:
    def test_list_orders_returns_200(self, client):
        response = client.get("/api/orders")
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data

    def test_create_order_returns_success(self, client):
        with patch("routes.orders.send_whatsapp_reply") as mock_reply:
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
        mock_reply.assert_called_once()
        assert mock_reply.call_args.args[0] == "+1234567890"


class TestActivityEndpoint:
    def test_activity_returns_200(self, client):
        response = client.get("/api/activity")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data


class TestBillingEndpoints:
    def test_billing_summary_returns_200(self, client):
        fake_summary = {
            "seller_id": "test-seller",
            "current_plan": "free",
            "plans": [],
            "usage": {
                "period_start": "2026-03-01",
                "products": {"used": 10, "limit": 100, "remaining": 90},
                "whatsapp_messages": {"used": 20, "limit": 100, "remaining": 80},
            },
        }
        with patch("routes.billing.get_billing_summary", return_value=fake_summary):
            response = client.get("/api/billing/summary?seller_id=test-seller")
        assert response.status_code == 200
        assert response.json()["current_plan"] == "free"

    def test_billing_checkout_returns_manual_contact_when_payment_not_configured(self, client):
        with patch(
            "routes.billing.create_razorpay_order",
            side_effect=BillingError(
                "PAYMENT_NOT_CONFIGURED",
                "Razorpay is not configured yet. We recorded your upgrade request.",
                status_code=503,
            ),
        ):
            response = client.post(
                "/api/billing/checkout",
                json={"seller_id": "test-seller", "plan": "pro"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "manual_contact_required"
        assert data["plan"] == "pro"


class TestAuthHelpers:
    def test_send_whatsapp_reply_uses_runtime_env(self, monkeypatch):
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_runtime")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "runtime-token")
        monkeypatch.setenv("TWILIO_WHATSAPP_FROM", "whatsapp:+15551234567")

        from routes.auth import send_whatsapp_reply

        with patch("twilio.rest.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            ok = send_whatsapp_reply("+15557654321", "hello")

        assert ok is True
        mock_client_cls.assert_called_once_with("AC_runtime", "runtime-token")
        mock_client.messages.create.assert_called_once_with(
            body="hello",
            from_="whatsapp:+15551234567",
            to="whatsapp:+15557654321",
        )

    def test_verify_twilio_signature_uses_public_url_override(self):
        from routes.auth import verify_twilio_signature

        request = MagicMock()
        request.headers.get.side_effect = lambda key, default="": {
            "x-twilio-signature": "sig-123",
            "host": "internal.railway.local",
            "x-forwarded-host": "public.up.railway.app",
            "x-forwarded-proto": "https",
        }.get(key, default)
        request.url.path = "/whatsapp-webhook"
        request.url.query = "foo=bar"

        with patch(
            "routes.auth.get_env_value",
            side_effect=lambda key, default="": {
                "PUBLIC_URL": "https://catalog.example.com",
                "TWILIO_AUTH_TOKEN": "auth-token",
            }.get(key, default),
        ), patch("twilio.request_validator.RequestValidator") as mock_validator_cls:
            mock_validator = MagicMock()
            mock_validator.validate.return_value = True
            mock_validator_cls.return_value = mock_validator

            ok = verify_twilio_signature(request, {"Body": "hello"})

        assert ok is True
        mock_validator.validate.assert_called_once_with(
            "https://catalog.example.com/whatsapp-webhook?foo=bar",
            {"Body": "hello"},
            "sig-123",
        )

    def test_verify_twilio_signature_fails_closed_in_production_when_validator_missing(self, monkeypatch):
        from routes.auth import verify_twilio_signature

        monkeypatch.setenv("NODE_ENV", "production")

        request = MagicMock()
        request.headers.get.side_effect = lambda key, default="": {
            "x-twilio-signature": "sig-123",
            "host": "catalog.example.com",
        }.get(key, default)
        request.url.path = "/whatsapp-webhook"
        request.url.query = ""

        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "twilio.request_validator":
                raise ImportError("missing twilio")
            return original_import(name, *args, **kwargs)

        with patch(
            "routes.auth.get_env_value",
            side_effect=lambda key, default="": {
                "PUBLIC_URL": "https://catalog.example.com",
                "TWILIO_AUTH_TOKEN": "auth-token",
            }.get(key, default),
        ), patch("builtins.__import__", side_effect=fake_import):
            ok = verify_twilio_signature(request, {"Body": "hello"})

        assert ok is False


class TestProductionValidation:
    def test_validate_production_env_requires_public_url(self, monkeypatch):
        from server import _validate_production_env

        monkeypatch.setenv("SUPABASE_URL", "https://project.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-key")
        monkeypatch.setenv("GROQ_API_KEY", "groq-key")
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC123")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
        monkeypatch.setenv("TWILIO_WHATSAPP_FROM", "whatsapp:+15551234567")
        monkeypatch.setenv("JWT_SECRET", "a-strong-secret")
        monkeypatch.delenv("PUBLIC_URL", raising=False)

        with pytest.raises(SystemExit) as exc:
            _validate_production_env()

        assert "PUBLIC_URL is not configured" in str(exc.value)
