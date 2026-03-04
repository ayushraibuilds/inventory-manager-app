"""
ONDC Beckn Protocol Adapter

Converts internal catalog format to ONDC-compliant /on_search response.
Follows the ONDC Beckn v1.1 specification for catalog publishing.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional


ONDC_DOMAIN = "nic2004:52110"  # Grocery domain code
ONDC_CITY = "*"                 # All cities
ONDC_COUNTRY = "IND"
BPP_ID = "ondc-super-seller.example.com"
BPP_URI = "https://ondc-super-seller.example.com/api/v1/ondc"

# ONDC category mapping
ONDC_CATEGORY_MAP = {
    "Grocery": {"id": "Grocery", "descriptor": {"name": "Grocery", "code": "grocery"}},
    "F&B": {"id": "F&B", "descriptor": {"name": "Food & Beverage", "code": "fnb"}},
    "Health & Wellness": {"id": "Health & Wellness", "descriptor": {"name": "Health & Wellness", "code": "health_wellness"}},
    "Beauty & Personal Care": {"id": "Beauty & Personal Care", "descriptor": {"name": "Beauty & Personal Care", "code": "beauty_personal_care"}},
    "Home & Decor": {"id": "Home & Decor", "descriptor": {"name": "Home & Decor", "code": "home_decor"}},
    "Electronics": {"id": "Electronics", "descriptor": {"name": "Electronics", "code": "electronics"}},
    "Other": {"id": "Other", "descriptor": {"name": "Other", "code": "other"}},
}


def build_context(action: str = "on_search", transaction_id: Optional[str] = None) -> dict:
    """Build ONDC Beckn context object."""
    return {
        "domain": ONDC_DOMAIN,
        "country": ONDC_COUNTRY,
        "city": ONDC_CITY,
        "action": action,
        "core_version": "1.1.0",
        "bpp_id": BPP_ID,
        "bpp_uri": BPP_URI,
        "transaction_id": transaction_id or str(uuid.uuid4()),
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def convert_item_to_ondc(item: dict, provider_id: str) -> dict:
    """Convert an internal catalog item to ONDC Beckn item format."""
    item_id = item.get("id", str(uuid.uuid4()))
    descriptor = item.get("descriptor", {})
    price = item.get("price", {})
    quantity = item.get("quantity", {})
    category_id = item.get("category_id", "Grocery")

    return {
        "id": item_id,
        "descriptor": {
            "name": descriptor.get("name", "Unknown"),
            "short_desc": descriptor.get("short_desc", ""),
            "long_desc": descriptor.get("short_desc", ""),
            "images": [],
        },
        "price": {
            "currency": price.get("currency", "INR"),
            "value": str(price.get("value", "0")),
            "maximum_value": str(float(price.get("value", "0")) * 1.1),  # 10% markup
        },
        "category_id": category_id,
        "quantity": {
            "available": {
                "count": quantity.get("available", {}).get("count", 0),
            },
            "maximum": {
                "count": quantity.get("available", {}).get("count", 0),
            },
        },
        "@ondc/org/returnable": True,
        "@ondc/org/cancellable": True,
        "@ondc/org/return_window": "P7D",
        "@ondc/org/seller_pickup_return": True,
        "@ondc/org/time_to_ship": "P1D",
        "@ondc/org/available_on_cod": False,
        "fulfillment_id": f"fulfillment_{provider_id}",
        "location_id": f"location_{provider_id}",
    }


def build_on_search_response(
    seller_id: str,
    catalog: dict,
    seller_profile: Optional[dict] = None,
    transaction_id: Optional[str] = None,
) -> dict:
    """
    Build a complete ONDC /on_search response from seller's catalog.

    Args:
        seller_id: UUID of the seller
        catalog: Internal Beckn catalog dict
        seller_profile: Seller profile (store_name, address, gst_number, phone, etc.)
        transaction_id: Optional transaction ID from incoming /search request

    Returns:
        ONDC-compliant on_search response dict
    """
    context = build_context("on_search", transaction_id)
    profile = seller_profile or {}

    store_name = profile.get("store_name", f"Super Seller: {seller_id}")
    address = profile.get("address", "India")
    gst_number = profile.get("gst_number", "")
    phone = profile.get("phone", "")

    # Extract items from internal catalog
    try:
        internal_items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError):
        internal_items = []

    provider_id = f"provider_{seller_id}"

    # Convert items
    ondc_items = [convert_item_to_ondc(item, provider_id) for item in internal_items]

    # Collect unique categories
    category_ids = set(item.get("category_id", "Grocery") for item in internal_items)
    categories = [ONDC_CATEGORY_MAP.get(cid, ONDC_CATEGORY_MAP["Other"]) for cid in category_ids]

    provider = {
        "id": provider_id,
        "descriptor": {
            "name": store_name,
            "short_desc": f"Catalog powered by ONDC Super Seller",
            "long_desc": f"{store_name} — managed via WhatsApp + AI",
            "images": [],
        },
        "locations": [
            {
                "id": f"location_{provider_id}",
                "gps": "",  # Seller can add GPS later
                "address": {
                    "street": address,
                    "city": "",
                    "state": "",
                    "area_code": "",
                    "country": "IND",
                },
            }
        ],
        "fulfillments": [
            {
                "id": f"fulfillment_{provider_id}",
                "type": "Delivery",
                "contact": {"phone": phone, "email": ""},
            }
        ],
        "categories": categories,
        "items": ondc_items,
        "tags": [
            {"code": "catalog_link", "list": [{"code": "type", "value": "inline"}]},
        ],
    }

    if gst_number:
        provider["tags"].append(
            {"code": "tax_id", "list": [{"code": "gst", "value": gst_number}]}
        )

    return {
        "context": context,
        "message": {
            "catalog": {
                "bpp/descriptor": {
                    "name": "ONDC Super Seller",
                    "short_desc": "AI-powered WhatsApp catalog management",
                    "long_desc": "Manage your ONDC catalog via WhatsApp messages and voice notes, powered by AI.",
                    "images": [],
                },
                "bpp/providers": [provider],
            }
        },
    }
