"""Unit tests for sanitize_product() and Pydantic validators."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent import sanitize_product


class FakeProduct:
    """Minimal mock product with settable attributes."""

    def __init__(self, name="Test", price_inr="100", quantity_value=5):
        self.name = name
        self.price_inr = price_inr
        self.quantity_value = quantity_value


class TestSanitizeProduct:
    def test_strips_html_tags(self):
        p = FakeProduct(name="<b>Atta</b> <script>alert(1)</script>Brand")
        result = sanitize_product(p)
        assert "<" not in result.name
        assert ">" not in result.name
        assert "script" not in result.name
        assert "Atta" in result.name

    def test_strips_special_characters(self):
        p = FakeProduct(name="Atta@#$%^&*!")
        result = sanitize_product(p)
        assert "@" not in result.name
        assert "#" not in result.name
        assert "Atta" in result.name

    def test_preserves_hyphens_and_spaces(self):
        p = FakeProduct(name="Aashirvaad Whole-Wheat Atta")
        result = sanitize_product(p)
        assert result.name == "Aashirvaad Whole-Wheat Atta"

    def test_negative_price_strips_sign(self):
        # sanitize_product strips non-numeric chars including '-', so -50 → 50
        p = FakeProduct(price_inr="-50")
        result = sanitize_product(p)
        assert result.price_inr == "50"

    def test_zero_price_stays_zero(self):
        p = FakeProduct(price_inr="0")
        result = sanitize_product(p)
        assert result.price_inr == "0"

    def test_valid_price_preserved(self):
        p = FakeProduct(price_inr="450")
        result = sanitize_product(p)
        assert result.price_inr == "450"

    def test_price_with_currency_symbol(self):
        p = FakeProduct(price_inr="₹450")
        result = sanitize_product(p)
        assert result.price_inr == "450"

    def test_price_with_letters(self):
        p = FakeProduct(price_inr="450rupees")
        result = sanitize_product(p)
        assert result.price_inr == "450"

    def test_negative_quantity_becomes_zero(self):
        p = FakeProduct(quantity_value=-10)
        result = sanitize_product(p)
        assert result.quantity_value == 0

    def test_zero_quantity_preserved(self):
        p = FakeProduct(quantity_value=0)
        result = sanitize_product(p)
        assert result.quantity_value == 0

    def test_valid_quantity_preserved(self):
        p = FakeProduct(quantity_value=25)
        result = sanitize_product(p)
        assert result.quantity_value == 25

    def test_empty_name_stripped(self):
        p = FakeProduct(name="   ")
        result = sanitize_product(p)
        assert result.name == ""

    def test_non_numeric_price_becomes_zero(self):
        p = FakeProduct(price_inr="free")
        result = sanitize_product(p)
        assert result.price_inr == "0"
