from datetime import datetime
from typing import TypedDict, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, START, END
import uuid
import os
import re
import difflib
import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from db import get_catalog, save_catalog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()
logger = logging.getLogger(__name__)
GLOBAL_LLM = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)


def _llm_invoke_with_retry(structured_llm, prompt: str, label: str = "LLM"):
    """Invoke a structured LLM with retry logic (3 attempts, exponential backoff)."""
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=8),
        retry=retry_if_exception_type(Exception),
        before_sleep=lambda retry_state: logger.warning(
            f"{label} attempt {retry_state.attempt_number} failed, retrying..."
        ),
    )
    def _invoke():
        return structured_llm.invoke(prompt)

    return _invoke()

class AgentState(TypedDict, total=False):
    raw_whatsapp_input: str
    seller_id: str
    intent: str
    translated_text: str
    detected_language: str
    conversation_history: list
    extracted_product_entities: Any
    ondc_beckn_json: Dict[str, Any]
    faq_answer: str

class ProductEntity(BaseModel):
    name: str = Field(description="The name of the product or item.")
    price_inr: str = Field(description="The price of the item in INR. Extract just the number as a string.")
    quantity_value: int = Field(description="The numerical quantity the seller has available.")
    unit: str = Field(description="The unit of measurement (e.g., kg, liter, pieces, packets).")
    category_id: Literal["Grocery", "F&B", "Home & Decor", "Health & Wellness", "Electronics", "Beauty & Personal Care", "Other"] = Field(default="Grocery", description="The ONDC category this item belongs to. Default to Grocery if unsure.")

class CatalogExtraction(BaseModel):
    items: List[ProductEntity] = Field(description="A list of all products mentioned in the message.")

class IntentClassifier(BaseModel):
    action: Literal["ADD", "UPDATE", "DELETE", "FAQ", "UNKNOWN"] = Field(
        description="The goal of the shopkeeper's message. ADD if listing new items. UPDATE if changing existing items' price/stock. DELETE if removing an item or saying it is out of stock. FAQ if asking a question about how to use the system, pricing, or ONDC. UNKNOWN if unclear."
    )

class DeleteTarget(BaseModel):
    item_id: str = Field(description="The exact ID of the item the user wants to delete.")

class UpdateTarget(BaseModel):
    item_id: str = Field(description="The exact ID of the item the user wants to update.")
    new_price_inr: Optional[int] = Field(default=None, description="The new numerical price in INR. Null if not mentioned.")
    new_quantity_value: Optional[int] = Field(default=None, description="The new numerical quantity. Null if not mentioned.")

def sanitize_product(item: Any) -> Any:
    """Sanitize LLM-extracted product data before writing to catalog."""
    if hasattr(item, 'name'):
        name = str(item.name)
        name = re.sub(r'<[^>]+>', '', name)  # Strip HTML
        name = re.sub(r'[^\w\s\-]', '', name)  # Strip special chars
        item.name = name.strip()
    if hasattr(item, 'price_inr'):
        try:
            price_val = float(re.sub(r'[^\d.]', '', str(item.price_inr)))
            if price_val <= 0:
                price_val = 0
            item.price_inr = str(int(price_val)) if price_val == int(price_val) else str(price_val)
        except (ValueError, TypeError):
            item.price_inr = "0"
    if hasattr(item, 'quantity_value'):
        try:
            if int(item.quantity_value) < 0:
                item.quantity_value = 0
        except (ValueError, TypeError):
            item.quantity_value = 0
    return item

# --- Language hints appended to LLM prompts per detected language ---
LANG_HINTS = {
    "hi": "\n\nLANGUAGE CONTEXT: The user speaks Hindi/Hinglish. Keywords: 'rakh do'=set/add, 'hata do'=remove, 'badal do'=change, 'karo'=do, 'chahiye'=need, 'wala'=of/with.",
    "en": "\n\nLANGUAGE CONTEXT: The user speaks English.",
    "ta": "\n\nLANGUAGE CONTEXT: The user speaks Tamil. Keywords: 'add pannunga'=add, 'neekkuunga'=remove.",
    "te": "\n\nLANGUAGE CONTEXT: The user speaks Telugu.",
    "kn": "\n\nLANGUAGE CONTEXT: The user speaks Kannada.",
    "bn": "\n\nLANGUAGE CONTEXT: The user speaks Bengali.",
}

def _format_conversation_context(history: list) -> str:
    """Format conversation history as a prompt prefix."""
    if not history:
        return ""
    lines = []
    for turn in history:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        prefix = "Seller" if role == "user" else "Assistant"
        lines.append(f"{prefix}: {content}")
    return "Recent conversation:\n" + "\n".join(lines) + "\n\n"

def detect_language(state: AgentState) -> Dict[str, Any]:
    """LangGraph node: detect the language of the incoming message."""
    from lang_detect import detect
    text = state.get("raw_whatsapp_input", "")
    result = detect(text)
    logger.info(f"Language detected: {result.lang_code} (method={result.method}, confidence={result.confidence})")
    return {"detected_language": result.lang_code}

def classify_intent(state: AgentState) -> Dict[str, Any]:
    text = state.get("raw_whatsapp_input", "")
    lang = state.get("detected_language", "en")
    history = state.get("conversation_history", [])
    
    structured_llm = GLOBAL_LLM.with_structured_output(IntentClassifier)
    
    context = _format_conversation_context(history)
    lang_hint = LANG_HINTS.get(lang, "")
    
    prompt = f"""
    You are an intent classifier for a shopkeeper inventory system.
    Analyze the following message and determine the user's intent.
    
    {context}Message: "{text}"
    
    Rules:
    - ADD: ALWAYS use this for terms like "rakh do", "set karo", "laga do", "aa gaye hain", or "add". Because ADD has smart upsert logic, always prefer ADD when the user is setting a price or listing stock.
    - UPDATE: ONLY use this if explicitly asked to specifically 'modify', 'change', or 'update' an existing item without mentioning full inventory listing.
    - DELETE: Triggered STRICTLY by terms like "hata do", "remove", "delete", "khatam ho gaya", "nikal do". ONLY use DELETE if they are completely removing an item or it is perfectly out of stock.
    - FAQ: Use this if the user is asking a question like "how to use", "kaise karu", "help", "pricing", "ONDC kya hai", or any general question not about managing inventory.
    - If it's none of the above, intent is UNKNOWN.
    {lang_hint}
    """
    
    try:
        result = _llm_invoke_with_retry(structured_llm, prompt, label="IntentClassifier")
        intent = getattr(result, 'action', 'UNKNOWN')
    except Exception as e:
        logger.error(f"Intent classification failed after retries: {e}")
        raise RuntimeError("LLM_API_ERROR")
        
    print(f"Detected Intent: {intent}")
    return {"intent": intent}

def parse_input(state: AgentState) -> Dict[str, Any]:
    text = state.get("raw_whatsapp_input", "")
    lang = state.get("detected_language", "en")
    history = state.get("conversation_history", [])
    
    # LLM based extraction using global Ollama model
    structured_llm = GLOBAL_LLM.with_structured_output(CatalogExtraction)
    
    context = _format_conversation_context(history)
    lang_hint = LANG_HINTS.get(lang, "")
    
    prompt = f"""
    Extract the product inventory details from the following message from a shopkeeper:
    
    {context}Message: "{text}"
    
    CRITICAL INSTRUCTIONS FOR HINGLISH:
    - If a unit is not explicitly mentioned, assume "piece".
    - Distinguish between the product's descriptive weight and the actual inventory count. 
    - E.g. "25 kilo wali 4 bori" -> The product is "25 kilo bori", the quantity is 4, unit is "bori" (or sack). Do NOT set quantity to 25.
    - Clean up misspellings dynamically (e.g. "namk" -> "salt" or "namak", "pkt" -> "packet").
    - VERY IMPORTANT: For `price_inr`, ONLY extract pure numbers. Strip all symbols like $, >=, rupees, or letters. Just the number (e.g. "14").
    
    CATEGORIZATION RULES (use these to assign category_id accurately):
    - "Grocery": rice, atta, dal, oil, sugar, salt, spices, dry fruits, packaged staples, flour, ghee
    - "F&B": ready-to-eat (Maggi, noodles), beverages (Coke, juice, tea, coffee), snacks (chips, biscuits, namkeen), bakery, dairy (milk, curd, paneer), frozen meals
    - "Health & Wellness": medicines, supplements, sanitizers, masks, handwash, first aid, vitamins
    - "Beauty & Personal Care": soap, shampoo, cosmetics, skincare, toothpaste, deodorant, hair oil
    - "Home & Decor": cleaning supplies (Harpic, Lizol, detergent), utensils, bedding, mops, brooms
    - "Electronics": chargers, earphones, bulbs, batteries, cables, adapters
    - Default to "Grocery" ONLY if no other category clearly fits.
    
    BULK INPUT RULES:
    - If the message lists many items separated by commas, "aur", "and", or newlines, extract ALL of them as separate items.
    - Example: "atta 450, dal 120, chawal 80, maggi 60" → 4 separate items
    - Do NOT merge items. Each product gets its own entry with its own price/quantity.
    - For very long lists, extract every single item mentioned. Do not summarize or skip any.
    {lang_hint}
    """
    
    try:
        result = _llm_invoke_with_retry(structured_llm, prompt, label="EntityExtractor")
    except Exception as e:
        logger.error(f"Entity extraction failed after retries: {e}")
        raise RuntimeError("LLM_API_ERROR")
        
    return {
        "translated_text": str(text).lower(),
        "extracted_product_entities": result
    }

def generate_beckn_catalog(state: AgentState) -> Dict[str, Any]:
    seller_id = state.get("seller_id", "unknown_seller")
    
    # Retrieve the extracted Pydantic object from the state
    extracted_data = state.get("extracted_product_entities")
    
    # 1. Fetch their past inventory from SQLite
    existing_catalog = get_catalog(seller_id)
    
    existing_items: List[Dict[str, Any]] = []
    try:
        fetched = existing_catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
        if isinstance(fetched, list):
            existing_items.extend(fetched)
    except (KeyError, IndexError, TypeError):
        pass

    if extracted_data and hasattr(extracted_data, 'items'):
        for item in getattr(extracted_data, 'items', []):
            item = sanitize_product(item)
            new_name = item.name.title()
            new_price = str(item.price_inr)
            new_qty = item.quantity_value
            new_unit = item.unit
            
            # Smart Merging: Check for highly similar name
            # Smart Merging: Check for highly similar name
            matched_item: Optional[Any] = None
            for ex_item in existing_items:
                if isinstance(ex_item, dict):
                    ex_desc = ex_item.get("descriptor")
                    ex_name = ex_desc.get("name", "") if isinstance(ex_desc, dict) else ""
                    if isinstance(ex_name, str):
                        similarity = difflib.SequenceMatcher(None, new_name.lower(), ex_name.lower()).ratio()
                        if similarity > 0.7 or new_name.lower() in ex_name.lower() or ex_name.lower() in new_name.lower():
                            matched_item = ex_item
                            break
            
            if matched_item is not None and isinstance(matched_item, dict):
                # EXISTS: Add extracted quantity to existing quantity, overwrite old price
                try:
                    q_dict = matched_item.get("quantity", {})
                    if not isinstance(q_dict, dict): q_dict = {}
                    
                    current_qty = 0
                    a_dict = q_dict.get("available", {})
                    if isinstance(a_dict, dict):
                        current_qty = int(str(a_dict.get("count", 0) or 0))
                except (ValueError, TypeError):
                    current_qty = 0
                    
                new_total = current_qty + new_qty
                
                # Safely rebuild nested dicts
                mq = matched_item.get("quantity", {})
                if not isinstance(mq, dict): mq = {}
                ma = mq.get("available", {})
                if not isinstance(ma, dict): ma = {}
                ma["count"] = new_total
                mq["available"] = ma
                matched_item["quantity"] = mq
                
                mp = matched_item.get("price", {})
                if not isinstance(mp, dict): mp = {}
                mp["currency"] = "INR"
                mp["value"] = new_price
                matched_item["price"] = mp
                
                md = matched_item.get("descriptor", {})
                if not isinstance(md, dict): md = {}
                md["name"] = new_name
                md["short_desc"] = f"{new_total} {new_unit} of {new_name}"
                matched_item["descriptor"] = md
                if hasattr(item, 'category_id'):
                    matched_item["category_id"] = item.category_id
            else:
                # DOES NOT EXIST: Append as a new item
                beckn_item = {
                    "id": str(uuid.uuid4()),
                    "category_id": getattr(item, 'category_id', 'Grocery'),
                    "descriptor": {
                        "name": new_name,
                        "short_desc": f"{new_qty} {new_unit} of {new_name}",
                    },
                    "price": {
                        "currency": "INR",
                        "value": str(new_price)
                    },
                    "quantity": {
                        "available": {
                            "count": new_qty
                        }
                    }
                }
                existing_items.append(beckn_item)

    # Wrap the items in the official bpp/catalog Provider structure
    updated_catalog = {
        "bpp/catalog": {
            "bpp/providers": [
                {
                    "id": f"provider_{seller_id}",
                    "descriptor": {
                        "name": f"Super Seller: {seller_id}"
                    },
                    "items": existing_items
                }
            ]
        }
    }
    
    # 3. Save the updated master catalog back to the database
    save_catalog(seller_id, updated_catalog)
    
    return {"ondc_beckn_json": updated_catalog}

def update_item(state: AgentState) -> Dict[str, Any]:
    seller_id = state.get("seller_id", "unknown_seller")
    raw_input = state.get("raw_whatsapp_input", "")
    
    existing_catalog = get_catalog(seller_id)
    try:
        items = existing_catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError):
        items = []
        
    if not items:
        return {"translated_text": "Catalog is currently empty, nothing to update."}
        
    catalog_context = [{"id": item["id"], "name": item["descriptor"]["name"], "current_price": item["price"]["value"], "current_quantity": item["quantity"]["available"]["count"]} for item in items]
    
    prompt = f"""
    You are an intent parser for an inventory system.
    User request: "{raw_input}"
    Current inventory: {catalog_context}
    
    CRITICAL INSTRUCTIONS:
    - Identify the item the user wants to update from the inventory and return its exact item_id.
    - If the user mentions a new price, extract ONLY the numerical value and set new_price_inr.
    - If the user mentions a new quantity, extract the numerical value and set new_quantity_value.
    - Leave unspecified fields as null.
    """
    
    try:
        target = _llm_invoke_with_retry(
            GLOBAL_LLM.with_structured_output(UpdateTarget), prompt, label="UpdateParser"
        )
    except Exception as e:
        logger.error(f"Update intent parsing failed after retries: {e}")
        raise RuntimeError("LLM_API_ERROR")
        
    print(f"UPDATE Target Parsed: {target}")
    
    target_item_id = getattr(target, 'item_id', None)
    if target_item_id:
        for item in items:
            if item["id"] == target_item_id:
                new_price_inr = getattr(target, 'new_price_inr', None)
                if new_price_inr is not None:
                    item["price"]["value"] = str(new_price_inr)
                
                new_qty = getattr(target, 'new_quantity_value', None)
                if new_qty is not None:
                    item["quantity"]["available"]["count"] = int(new_qty)
                break
                
        existing_catalog["bpp/catalog"]["bpp/providers"][0]["items"] = items
        save_catalog(seller_id, existing_catalog)
        return {"ondc_beckn_json": existing_catalog}
        
    return {"translated_text": "Could not identify the item to update."}

def delete_item(state: AgentState) -> Dict[str, Any]:
    seller_id = state.get("seller_id", "unknown_seller")
    raw_input = state.get("raw_whatsapp_input", "")
    
    # Fetch the master catalog from SQLite
    existing_catalog = get_catalog(seller_id)
    try:
        items = existing_catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError):
        items = []
    
    if not items:
        return {"translated_text": "Catalog is already empty."}
        
    # Create a tiny, memory-efficient map for the LLM context window
    catalog_context = [{"id": item["id"], "name": item["descriptor"]["name"]} for item in items]
    prompt = f"User request: {raw_input}\nCurrent inventory: {catalog_context}\nReturn the exact item_id to delete."
    
    try:
        target = _llm_invoke_with_retry(
            GLOBAL_LLM.with_structured_output(DeleteTarget), prompt, label="DeleteParser"
        )
    except Exception as e:
        logger.error(f"Delete intent parsing failed after retries: {e}")
        raise RuntimeError("LLM_API_ERROR")
        
    print(f"DELETE Target Parsed: {target}")
    
    target_item_id = getattr(target, 'item_id', None)
    if target_item_id:
        # Python does the actual surgery to ensure perfect schema integrity
        updated_items = [item for item in items if item["id"] != target_item_id]
        existing_catalog["bpp/catalog"]["bpp/providers"][0]["items"] = updated_items
        
        save_catalog(seller_id, existing_catalog)
        return {"ondc_beckn_json": existing_catalog}
        
    return {"translated_text": "Could not match the item to delete."}

def route_intent(state: AgentState) -> str:
    return str(state.get("intent", "UNKNOWN"))

def handle_faq(state: AgentState) -> Dict[str, Any]:
    """LangGraph node: handle FAQ/support queries."""
    from reply_templates import get_faq_answer
    
    text = state.get("raw_whatsapp_input", "").lower()
    lang = state.get("detected_language", "en")
    
    # Simple keyword matching for FAQ topics
    if any(w in text for w in ["how to", "kaise", "use", "istamaal", "istemal"]):
        topic = "how_to_use"
    elif any(w in text for w in ["price", "pricing", "cost", "paisa", "kitna", "charge", "free"]):
        topic = "pricing"
    elif any(w in text for w in ["ondc", "what is", "kya hai"]):
        topic = "ondc"
    else:
        topic = "help"
    
    answer = get_faq_answer(lang, topic)
    return {"faq_answer": answer, "translated_text": answer}

# Build graph
builder = StateGraph(AgentState)
builder.add_node("detect_language", detect_language)
builder.add_node("classify_intent", classify_intent)
builder.add_node("parse_input", parse_input)
builder.add_node("generate_beckn_catalog", generate_beckn_catalog)
builder.add_node("update_item", update_item)
builder.add_node("delete_item", delete_item)
builder.add_node("handle_faq", handle_faq)

builder.add_edge(START, "detect_language")
builder.add_edge("detect_language", "classify_intent")

builder.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "ADD": "parse_input",
        "UPDATE": "update_item",
        "DELETE": "delete_item",
        "FAQ": "handle_faq",
        "UNKNOWN": END
    }
)

builder.add_edge("update_item", END)
builder.add_edge("delete_item", END)
builder.add_edge("handle_faq", END)
builder.add_edge("parse_input", "generate_beckn_catalog")
builder.add_edge("generate_beckn_catalog", END)

graph = builder.compile()

def process_whatsapp_message(message: str, seller_id: str = "unknown_seller", conversation_history: list = None) -> Dict[str, Any]:
    """Process an incoming WhatsApp message through the LangGraph state machine"""
    initial_state: AgentState = {
        "raw_whatsapp_input": message,
        "seller_id": seller_id,
        "conversation_history": conversation_history or [],
    }
    final_state = graph.invoke(initial_state)
    return final_state

if __name__ == "__main__":
    # Test script
    print(process_whatsapp_message("I have 10kg of apples for 150 rupees each"))
