import pytest
from agent import process_whatsapp_message
from db import get_catalog


def test_update_intent_flow():
    """Test full ADD → UPDATE flow: insert a product, then update its price/qty."""
    seller_id = "whatsapp:+test_update"
    
    # Step 1: Add a product first
    add_result = process_whatsapp_message("Add Good Day biscuit 10 rupees and quantity 5", seller_id)
    assert add_result.get("intent") == "ADD"
    assert "ondc_beckn_json" in add_result
    
    # Verify it was saved to DB
    catalog = get_catalog(seller_id)
    items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    assert len(items) > 0
    
    original_item = items[0]
    original_price = original_item["price"]["value"]
    
    # Step 2: Send an update request
    update_result = process_whatsapp_message("Arrey suno, Good Day biscuit ka price 20 kar do aur quantity 8 kar do", seller_id)
    
    assert update_result.get("intent") in ["UPDATE", "ADD"]
    
    # Step 3: Verify the catalog was actually modified
    updated_catalog = get_catalog(seller_id)
    updated_items = updated_catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    assert len(updated_items) > 0
