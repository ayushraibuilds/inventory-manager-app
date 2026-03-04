"""Tests for price intelligence module."""
import pytest
from price_reference import (
    get_price_suggestion,
    get_catalog_price_report,
    _fuzzy_find,
    PriceSuggestion,
    REFERENCE_PRICES,
)


class TestFuzzyFind:
    """Tests for the fuzzy item name matching."""

    def test_exact_match(self):
        assert _fuzzy_find("atta") == "atta"

    def test_exact_match_case_insensitive(self):
        assert _fuzzy_find("Atta") == "atta"

    def test_substring_match(self):
        assert _fuzzy_find("basmati") is not None

    def test_fuzzy_match(self):
        # "aata" is close to "atta"
        result = _fuzzy_find("aata")
        assert result is not None

    def test_no_match(self):
        assert _fuzzy_find("xyznonexistent") is None

    def test_wheat_flour(self):
        assert _fuzzy_find("wheat flour") == "wheat flour"


class TestGetPriceSuggestion:
    """Tests for price suggestion logic."""

    def test_competitive_price(self):
        result = get_price_suggestion("atta", 45, "kg")
        assert result is not None
        assert result.status == "competitive"

    def test_high_price(self):
        result = get_price_suggestion("atta", 100, "kg")
        assert result is not None
        assert result.status == "high"
        assert "💡" in result.suggestion

    def test_low_price(self):
        result = get_price_suggestion("atta", 10, "kg")
        assert result is not None
        assert result.status == "low"
        assert "💡" in result.suggestion

    def test_unknown_item(self):
        result = get_price_suggestion("quantum_flux_capacitor", 100, "piece")
        assert result is None

    def test_returns_pricsuggestion_type(self):
        result = get_price_suggestion("rice", 50, "kg")
        assert isinstance(result, PriceSuggestion)

    def test_market_range(self):
        result = get_price_suggestion("sugar", 45, "kg")
        assert result is not None
        assert result.market_range[0] <= result.market_range[1]

    def test_maggi_competitive(self):
        result = get_price_suggestion("maggi", 14, "piece")
        assert result is not None
        assert result.status == "competitive"

    def test_milk_high(self):
        result = get_price_suggestion("milk", 120, "liter")
        assert result is not None
        assert result.status == "high"


class TestCatalogPriceReport:
    """Tests for full catalog report."""

    def test_report_with_items(self):
        items = [
            {"descriptor": {"name": "Atta"}, "price": {"value": "45"}, "unit": "kg"},
            {"descriptor": {"name": "Rice"}, "price": {"value": "500"}, "unit": "kg"},
        ]
        report = get_catalog_price_report(items)
        assert isinstance(report, list)
        assert len(report) >= 1  # At least rice should trigger

    def test_empty_catalog(self):
        report = get_catalog_price_report([])
        assert report == []

    def test_unknown_items_skipped(self):
        items = [
            {"descriptor": {"name": "Alien Crystals"}, "price": {"value": "999"}, "unit": "piece"},
        ]
        report = get_catalog_price_report(items)
        assert report == []

    def test_report_structure(self):
        items = [
            {"descriptor": {"name": "Atta"}, "price": {"value": "100"}, "unit": "kg"},
        ]
        report = get_catalog_price_report(items)
        if report:
            entry = report[0]
            assert "item_name" in entry
            assert "seller_price" in entry
            assert "market_avg" in entry
            assert "status" in entry
            assert "suggestion" in entry
