import pytest
from agent import process_whatsapp_message


def test_intent_classification_add():
    """Verify that product listing messages get classified as ADD."""
    result = process_whatsapp_message("Mere paas 20 packet Maggi masala hai 14 rupees each", "whatsapp:+test_intent")
    
    assert result.get("intent") == "ADD"
    assert "ondc_beckn_json" in result
    assert "bpp/providers" in result["ondc_beckn_json"]["bpp/catalog"]


def test_intent_classification_complex():
    """Verify Hinglish complex message extraction."""
    result = process_whatsapp_message("Tata namk 1kg ke 50 pkt bache hn, 1 ka dam 20 rupay set kro.", "whatsapp:+test_intent")
    
    assert result.get("intent") in ["ADD", "UPDATE"]
    entities = result.get("extracted_product_entities")
    assert entities is not None
    item = entities.items[0]
    assert float(item.price_inr) == 20.0
    assert item.quantity_value == 50
