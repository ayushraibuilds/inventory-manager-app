import pytest
from agent import process_whatsapp_message


def test_hinglish_add_intent():
    """Verify Hinglish ADD intent with Aashirvaad atta pricing."""
    result = process_whatsapp_message("Bhaiya, 10 kilo Aashirvaad atta ka price 450 rupees rakh do.", "whatsapp:+test_hinglish")
    
    assert result.get("intent") in ["ADD", "UPDATE"], f"Unexpected intent: {result.get('intent')}"
    assert "extracted_product_entities" in result
    
    entities = result["extracted_product_entities"].items[0]
    assert "atta" in entities.name.lower()
    assert float(entities.price_inr) > 0
    assert entities.quantity_value > 0


def test_hinglish_complex_quantities():
    """Verify correct parsing of '25 kilo wali 4 bori' — quantity should be 4, not 25."""
    result = process_whatsapp_message("India gate basmati chawal ki 25 kilo wali 4 bori available hain, ek bori ka rate 2500 laga do.", "whatsapp:+test_hinglish")
    
    assert "extracted_product_entities" in result
    entities = result["extracted_product_entities"].items[0]
    assert entities.quantity_value == 4
    assert entities.unit.lower() in ["bori", "box", "bag", "sack"]
    assert float(entities.price_inr) == 2500.0
