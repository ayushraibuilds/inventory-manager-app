"""Tests for ONDC Beckn adapter."""
import pytest
from ondc_adapter import (
    build_context,
    convert_item_to_ondc,
    build_on_search_response,
    ONDC_CATEGORY_MAP,
    BPP_ID,
)


class TestBuildContext:
    def test_default_action(self):
        ctx = build_context()
        assert ctx["action"] == "on_search"
        assert ctx["core_version"] == "1.1.0"
        assert ctx["bpp_id"] == BPP_ID
        assert ctx["country"] == "IND"
        assert "transaction_id" in ctx
        assert "message_id" in ctx
        assert "timestamp" in ctx

    def test_custom_action(self):
        ctx = build_context("search")
        assert ctx["action"] == "search"

    def test_custom_transaction_id(self):
        ctx = build_context(transaction_id="txn-123")
        assert ctx["transaction_id"] == "txn-123"


class TestConvertItemToOndc:
    def test_basic_item(self):
        item = {
            "id": "item-1",
            "descriptor": {"name": "Atta", "short_desc": "10 kg"},
            "price": {"value": "45", "currency": "INR"},
            "quantity": {"available": {"count": 100}},
            "category_id": "Grocery",
        }
        result = convert_item_to_ondc(item, "provider-1")
        assert result["id"] == "item-1"
        assert result["descriptor"]["name"] == "Atta"
        assert result["price"]["currency"] == "INR"
        assert result["price"]["value"] == "45"
        assert result["quantity"]["available"]["count"] == 100
        assert result["category_id"] == "Grocery"
        assert result["@ondc/org/returnable"] is True
        assert result["@ondc/org/time_to_ship"] == "P1D"
        assert result["fulfillment_id"] == "fulfillment_provider-1"

    def test_missing_fields_defaults(self):
        item = {}
        result = convert_item_to_ondc(item, "prov-2")
        assert result["descriptor"]["name"] == "Unknown"
        assert result["price"]["value"] == "0"
        assert result["quantity"]["available"]["count"] == 0

    def test_maximum_value_markup(self):
        item = {"price": {"value": "100"}}
        result = convert_item_to_ondc(item, "prov-1")
        assert float(result["price"]["maximum_value"]) == pytest.approx(110.0, rel=1e-6)


class TestBuildOnSearchResponse:
    def _mock_catalog(self, items):
        return {"bpp/catalog": {"bpp/providers": [{"items": items}]}}

    def test_basic_response(self):
        catalog = self._mock_catalog([
            {"id": "1", "descriptor": {"name": "Rice"}, "price": {"value": "60"},
             "quantity": {"available": {"count": 50}}, "category_id": "Grocery"},
        ])
        resp = build_on_search_response("seller-1", catalog)
        assert resp["context"]["action"] == "on_search"
        providers = resp["message"]["catalog"]["bpp/providers"]
        assert len(providers) == 1
        assert len(providers[0]["items"]) == 1
        assert providers[0]["items"][0]["descriptor"]["name"] == "Rice"

    def test_empty_catalog(self):
        catalog = self._mock_catalog([])
        resp = build_on_search_response("seller-1", catalog)
        providers = resp["message"]["catalog"]["bpp/providers"]
        assert len(providers[0]["items"]) == 0

    def test_seller_profile(self):
        catalog = self._mock_catalog([])
        profile = {"store_name": "Test Store", "address": "123 Main St", "gst_number": "GST123", "phone": "+911234567890"}
        resp = build_on_search_response("seller-1", catalog, seller_profile=profile)
        provider = resp["message"]["catalog"]["bpp/providers"][0]
        assert provider["descriptor"]["name"] == "Test Store"
        gst_tags = [t for t in provider["tags"] if t["code"] == "tax_id"]
        assert len(gst_tags) == 1

    def test_no_gst_no_tag(self):
        catalog = self._mock_catalog([])
        profile = {"store_name": "Store", "gst_number": ""}
        resp = build_on_search_response("seller-1", catalog, seller_profile=profile)
        provider = resp["message"]["catalog"]["bpp/providers"][0]
        gst_tags = [t for t in provider["tags"] if t["code"] == "tax_id"]
        assert len(gst_tags) == 0

    def test_transaction_id_passthrough(self):
        catalog = self._mock_catalog([])
        resp = build_on_search_response("seller-1", catalog, transaction_id="txn-abc")
        assert resp["context"]["transaction_id"] == "txn-abc"

    def test_multiple_categories(self):
        catalog = self._mock_catalog([
            {"id": "1", "descriptor": {"name": "Rice"}, "price": {"value": "60"}, "quantity": {"available": {"count": 5}}, "category_id": "Grocery"},
            {"id": "2", "descriptor": {"name": "Soap"}, "price": {"value": "30"}, "quantity": {"available": {"count": 20}}, "category_id": "Beauty & Personal Care"},
        ])
        resp = build_on_search_response("seller-1", catalog)
        provider = resp["message"]["catalog"]["bpp/providers"][0]
        assert len(provider["items"]) == 2
        cat_ids = {c["id"] for c in provider["categories"]}
        assert "Grocery" in cat_ids
        assert "Beauty & Personal Care" in cat_ids

    def test_malformed_catalog_no_crash(self):
        resp = build_on_search_response("seller-1", {})
        providers = resp["message"]["catalog"]["bpp/providers"]
        assert len(providers[0]["items"]) == 0


class TestCategoryMap:
    def test_all_categories_have_descriptor(self):
        for cat_id, cat in ONDC_CATEGORY_MAP.items():
            assert "id" in cat
            assert "descriptor" in cat
            assert "name" in cat["descriptor"]
            assert "code" in cat["descriptor"]

    def test_known_categories(self):
        assert "Grocery" in ONDC_CATEGORY_MAP
        assert "F&B" in ONDC_CATEGORY_MAP
        assert "Electronics" in ONDC_CATEGORY_MAP
