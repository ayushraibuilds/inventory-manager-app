"""
Price intelligence for Indian grocery and retail items.

Provides market reference prices and generates suggestions when a seller's
price is significantly above or below average.
"""
import difflib
from dataclasses import dataclass
from typing import Optional, Tuple

# --- Reference prices (INR per standard unit) ---
# Source: Average Indian market prices as of 2024-2025
REFERENCE_PRICES = {
    # Grocery staples
    "atta": {"avg": 45, "unit": "kg", "range": (35, 55), "category": "Grocery"},
    "wheat flour": {"avg": 45, "unit": "kg", "range": (35, 55), "category": "Grocery"},
    "rice": {"avg": 50, "unit": "kg", "range": (30, 80), "category": "Grocery"},
    "basmati rice": {"avg": 90, "unit": "kg", "range": (60, 150), "category": "Grocery"},
    "dal": {"avg": 120, "unit": "kg", "range": (80, 160), "category": "Grocery"},
    "toor dal": {"avg": 130, "unit": "kg", "range": (100, 170), "category": "Grocery"},
    "moong dal": {"avg": 110, "unit": "kg", "range": (80, 150), "category": "Grocery"},
    "chana dal": {"avg": 90, "unit": "kg", "range": (70, 120), "category": "Grocery"},
    "sugar": {"avg": 45, "unit": "kg", "range": (38, 55), "category": "Grocery"},
    "salt": {"avg": 22, "unit": "kg", "range": (15, 30), "category": "Grocery"},
    "oil": {"avg": 150, "unit": "liter", "range": (110, 200), "category": "Grocery"},
    "mustard oil": {"avg": 170, "unit": "liter", "range": (140, 210), "category": "Grocery"},
    "sunflower oil": {"avg": 140, "unit": "liter", "range": (110, 180), "category": "Grocery"},
    "ghee": {"avg": 550, "unit": "kg", "range": (450, 700), "category": "Grocery"},
    "tea": {"avg": 300, "unit": "kg", "range": (200, 500), "category": "Grocery"},
    "coffee": {"avg": 400, "unit": "kg", "range": (250, 600), "category": "Grocery"},
    "turmeric": {"avg": 200, "unit": "kg", "range": (140, 300), "category": "Grocery"},
    "red chili powder": {"avg": 250, "unit": "kg", "range": (180, 350), "category": "Grocery"},
    "cumin": {"avg": 350, "unit": "kg", "range": (250, 500), "category": "Grocery"},
    "coriander powder": {"avg": 150, "unit": "kg", "range": (100, 220), "category": "Grocery"},
    "besan": {"avg": 80, "unit": "kg", "range": (60, 110), "category": "Grocery"},
    "maida": {"avg": 40, "unit": "kg", "range": (30, 55), "category": "Grocery"},
    "sooji": {"avg": 45, "unit": "kg", "range": (35, 60), "category": "Grocery"},
    "poha": {"avg": 50, "unit": "kg", "range": (35, 65), "category": "Grocery"},
    "jaggery": {"avg": 60, "unit": "kg", "range": (40, 80), "category": "Grocery"},

    # F&B / Snacks
    "maggi": {"avg": 14, "unit": "piece", "range": (12, 16), "category": "F&B"},
    "noodles": {"avg": 14, "unit": "piece", "range": (10, 20), "category": "F&B"},
    "biscuit": {"avg": 30, "unit": "piece", "range": (10, 60), "category": "F&B"},
    "chips": {"avg": 20, "unit": "piece", "range": (10, 40), "category": "F&B"},
    "namkeen": {"avg": 40, "unit": "piece", "range": (20, 80), "category": "F&B"},
    "bread": {"avg": 40, "unit": "piece", "range": (25, 60), "category": "F&B"},
    "milk": {"avg": 56, "unit": "liter", "range": (46, 70), "category": "F&B"},
    "curd": {"avg": 30, "unit": "piece", "range": (20, 50), "category": "F&B"},
    "paneer": {"avg": 350, "unit": "kg", "range": (280, 450), "category": "F&B"},
    "butter": {"avg": 50, "unit": "piece", "range": (40, 70), "category": "F&B"},
    "eggs": {"avg": 7, "unit": "piece", "range": (5, 10), "category": "F&B"},
    "coke": {"avg": 40, "unit": "piece", "range": (20, 60), "category": "F&B"},
    "pepsi": {"avg": 40, "unit": "piece", "range": (20, 60), "category": "F&B"},
    "juice": {"avg": 25, "unit": "piece", "range": (15, 40), "category": "F&B"},

    # Personal care
    "soap": {"avg": 40, "unit": "piece", "range": (20, 80), "category": "Beauty & Personal Care"},
    "shampoo": {"avg": 150, "unit": "piece", "range": (50, 400), "category": "Beauty & Personal Care"},
    "toothpaste": {"avg": 80, "unit": "piece", "range": (30, 150), "category": "Beauty & Personal Care"},

    # Home
    "detergent": {"avg": 100, "unit": "kg", "range": (60, 180), "category": "Home & Decor"},
}

# Threshold for "off-market" pricing (30% above or below average)
PRICE_ALERT_THRESHOLD = 0.30


@dataclass
class PriceSuggestion:
    item_name: str
    seller_price: float
    market_avg: float
    market_range: Tuple[float, float]
    unit: str
    status: str       # "competitive", "high", "low"
    suggestion: str   # human-readable hint


def _fuzzy_find(item_name: str) -> Optional[str]:
    """Find the closest matching reference item using fuzzy matching."""
    name_lower = item_name.lower().strip()

    # Exact match
    if name_lower in REFERENCE_PRICES:
        return name_lower

    # Substring match
    for ref_name in REFERENCE_PRICES:
        if ref_name in name_lower or name_lower in ref_name:
            return ref_name

    # Fuzzy match
    matches = difflib.get_close_matches(name_lower, REFERENCE_PRICES.keys(), n=1, cutoff=0.6)
    return matches[0] if matches else None


def get_price_suggestion(item_name: str, price: float, unit: str = "") -> Optional[PriceSuggestion]:
    """
    Check a seller's price against market reference data.
    Returns a PriceSuggestion if the item is found in REFERENCE_PRICES, else None.
    """
    ref_key = _fuzzy_find(item_name)
    if not ref_key:
        return None

    ref = REFERENCE_PRICES[ref_key]
    avg = ref["avg"]
    low, high = ref["range"]
    ref_unit = ref["unit"]

    # Determine status
    if price > avg * (1 + PRICE_ALERT_THRESHOLD):
        status = "high"
        suggestion = f"💡 Your price ₹{price:.0f}/{ref_unit} is above market avg ₹{avg}/{ref_unit}. Range: ₹{low}–₹{high}."
    elif price < avg * (1 - PRICE_ALERT_THRESHOLD):
        status = "low"
        suggestion = f"💡 Your price ₹{price:.0f}/{ref_unit} is below market avg ₹{avg}/{ref_unit}. You might be underpricing!"
    else:
        status = "competitive"
        suggestion = f"✅ ₹{price:.0f}/{ref_unit} is competitive (market avg: ₹{avg})."

    return PriceSuggestion(
        item_name=item_name,
        seller_price=price,
        market_avg=avg,
        market_range=(low, high),
        unit=ref_unit,
        status=status,
        suggestion=suggestion,
    )


def get_catalog_price_report(items: list) -> list:
    """
    Generate price suggestions for a list of catalog items.
    Each item should have: name, price (value), and optionally unit.
    Returns list of PriceSuggestion dicts.
    """
    suggestions = []
    for item in items:
        try:
            name = item.get("descriptor", {}).get("name", "")
            price = float(item.get("price", {}).get("value", 0))
            unit = item.get("unit", "")
            item_id = item.get("id", "")
            if not name or price <= 0:
                continue

            result = get_price_suggestion(name, price, unit)
            if result:
                suggestions.append({
                    "item_id": item_id,
                    "item_name": result.item_name,
                    "seller_price": result.seller_price,
                    "market_avg": result.market_avg,
                    "market_range": list(result.market_range),
                    "unit": result.unit,
                    "status": result.status,
                    "suggestion": result.suggestion,
                })
        except (ValueError, TypeError, AttributeError):
            continue

    return suggestions
