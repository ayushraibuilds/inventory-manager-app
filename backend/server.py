from fastapi import FastAPI, Request, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator
import asyncio
from typing import Dict, Any, Optional, List
import logging
import uuid
import re
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Filter out the Next.js polling spam from the uvicorn access logger
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /api/catalog") == -1

logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

from agent import process_whatsapp_message
from db import (
    get_all_catalogs, get_catalog, save_catalog,
    get_all_seller_ids, log_activity, get_activity_logs,
    save_seller_profile, get_seller_profile,
    create_order, get_orders, update_order_status,
    get_seller_id_by_phone
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- Auth helpers ---
API_KEY = os.getenv("API_KEY", "")
security = HTTPBearer(auto_error=False)

async def get_jwt_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    if credentials:
        return credentials.credentials
    return None

TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")

async def verify_api_key(x_api_key: str = Header(default="")):
    """Dependency that verifies the X-API-Key header on write endpoints."""
    if not API_KEY:
        return  # No key configured = dev mode, skip auth
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

def verify_twilio_signature(request: Request, form_data: dict) -> bool:
    """Validates Twilio webhook signature. Returns True if valid or if auth is disabled."""
    if not TWILIO_AUTH_TOKEN:
        return True  # Dev mode — skip validation
    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        return validator.validate(url, form_data, signature)
    except ImportError:
        logging.warning("twilio package not installed, skipping webhook validation")
        return True

def send_whatsapp_reply(to: str, body: str):
    """Send a WhatsApp reply via Twilio. Silently fails if not configured."""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_FROM:
        logging.info(f"[DEV MODE] WhatsApp reply to {to}: {body}")
        return
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=body,
            from_=TWILIO_WHATSAPP_FROM,
            to=to
        )
    except Exception as e:
        logging.error(f"Failed to send WhatsApp reply: {e}")

# --- Pydantic models ---
class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ItemCreate(BaseModel):
    name: str
    price: str
    quantity: int = Field(ge=0)
    unit: str
    seller_id: str
    category_id: str = "Grocery"

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        v = re.sub(r'<[^>]+>', '', v)
        v = re.sub(r'[^\w\s\-]', '', v)
        return v.strip()

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: str) -> str:
        try:
            if float(v) <= 0: raise ValueError("Price must be > 0")
        except ValueError:
            raise ValueError("Price must be a number > 0")
        return str(v)

class ItemUpdate(BaseModel):
    seller_id: str
    name: Optional[str] = None
    price: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=0)
    unit: Optional[str] = None

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None: return v
        v = re.sub(r'<[^>]+>', '', v)
        v = re.sub(r'[^\w\s\-]', '', v)
        return v.strip()

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Optional[str]) -> Optional[str]:
        if v is None: return v
        try:
            if float(v) <= 0: raise ValueError("Price must be > 0")
        except ValueError:
            raise ValueError("Price must be a number > 0")
        return str(v)

class BulkDeleteRequest(BaseModel):
    seller_id: str
    item_ids: List[str]

class SellerProfileUpdate(BaseModel):
    store_name: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    low_stock_alerts: Optional[bool] = None

class OrderCreate(BaseModel):
    seller_id: str
    buyer_name: str = ""
    buyer_phone: str = ""
    items: List[Dict[str, Any]] = Field(default_factory=list)
    total_amount: float = 0

class OrderStatusUpdate(BaseModel):
    status: str = Field(description="One of: PLACED, ACCEPTED, SHIPPED, DELIVERED, CANCELLED")

class CatalogImportItem(BaseModel):
    name: str
    price: str
    quantity: int = Field(ge=0)
    unit: str = "piece"
    category_id: str = "Grocery"

class CatalogImport(BaseModel):
    seller_id: str
    items: List[CatalogImportItem]

# --- App setup ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(application: FastAPI):
    """Modern lifespan handler replacing deprecated @app.on_event."""
    task = asyncio.create_task(check_low_stock_alerts())
    yield
    task.cancel()

app = FastAPI(title="ONDC Super Seller API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3005", "http://127.0.0.1:3000", "http://192.168.1.34:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Webhook with WhatsApp reply ---
@app.post("/whatsapp-webhook")
@limiter.limit("30/minute")
async def whatsapp_webhook(request: Request):
    token = None
    """
    Webhook to receive incoming WhatsApp messages.
    Processes the message through the AI agent and sends a reply.
    """
    try:
        form_data = await request.form()
        form_dict = dict(form_data)
        seller_id = form_dict.get("From", "unknown_seller")
        raw_message = form_dict.get("Body", "")
        
        if not verify_twilio_signature(request, form_dict):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    except HTTPException:
        raise
    except Exception:
        try:
            json_data = await request.json()
            seller_id = json_data.get("from_number", "unknown_seller")
            raw_message = json_data.get("message", "")
        except Exception:
            seller_id = "unknown_seller"
            raw_message = ""
            
    # --- Phase 2: Voice Note Interception ---
    try:
        num_media = int(form_dict.get("NumMedia", 0))
        if num_media > 0:
            content_type = form_dict.get("MediaContentType0", "")
            if content_type.startswith("audio/"):
                media_url = form_dict.get("MediaUrl0")
                if media_url:
                    from voice_processor import voice_processor
                    transcription = await voice_processor.transcribe_audio(media_url)
                    print(f"🎤 Voice Note Transcribed: {transcription}")
                    if transcription:
                        raw_message = transcription
    except Exception as e:
        print(f"Voice Note Error: {e}")
        await asyncio.to_thread(send_whatsapp_reply, seller_id, "⚠️ We couldn't transcribe your voice note at the moment. Please send a text message instead.") # type: ignore
        return {"status": "error", "message": "Voice Transcription Error"}
    
    # --- Phone to UUID Resolution ---
    extracted_phone = seller_id.replace("whatsapp:", "").replace("+", "")
    # Attempt to locate the exact seller profile UUID using the phone number
    real_seller_id = get_seller_id_by_phone(extracted_phone)
    if not real_seller_id:
        print(f"Unknown phone number: {extracted_phone}")
        # The seller doesn't exist natively. Tell them to sign up!
        reply = "⚠️ Welcome! To create an ONDC catalog, please sign up through our Super Seller Dashboard and link your phone number first."
        await asyncio.to_thread(send_whatsapp_reply, seller_id, reply) # type: ignore
        return {"status": "error", "message": "Unregistered Seller Phone"}
        
    # We found the seller, swap the Twilio ID out for their database UUID for all downstream operations!
    seller_id = real_seller_id
    
    # --- Feature 16: Seller Onboarding ---
    profile = get_seller_profile(seller_id)
    if not profile.get("store_name"):
        welcome = (
            "🎉 *Welcome to ONDC Super Seller!*\n\n"
            "I'm your AI catalog assistant. Just tell me what you sell in Hindi or English:\n\n"
            "• \"10 kg atta for 450 rupees\"\n"
            "• \"5 packet Maggi at 60 each\"\n\n"
            "I'll create your ONDC catalog automatically! 📱\n\n"
            "_Tip: Visit the dashboard to set your store name and address._"
        )
        await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", welcome) # type: ignore
        log_activity(seller_id, "SELLER_ONBOARDED", details="New seller interacted", jwt_token=token)
    
    try:
        result = await asyncio.to_thread(process_whatsapp_message, raw_message, seller_id) # type: ignore
    except Exception as e:
        print(f"Agent Processing Error: {e}")
        reply = "⚠️ Sorry, our AI is currently experiencing high traffic or a timeout. Please try again in a moment."
        await asyncio.to_thread(send_whatsapp_reply, seller_id, reply) # type: ignore
        return {"status": "error", "message": "LLM API Error"}
    
    # Build and send WhatsApp reply
    intent = result.get("intent", "UNKNOWN")
    reply = ""
    
    if intent == "ADD":
        catalog = result.get("ondc_beckn_json", {})
        try:
            items = catalog.get("bpp/catalog", {}).get("bpp/providers", [{}])[0].get("items", [])
            item_count = len(items)
            entities = result.get("extracted_product_entities")
            if entities and hasattr(entities, 'items') and len(entities.items) > 0:
                names = [f"{e.name} (₹{e.price_inr} × {e.quantity_value} {e.unit})" for e in entities.items]
                reply = f"✅ Added: {', '.join(names)}.\nYour catalog now has {item_count} items."
            else:
                reply = f"✅ Catalog updated. You now have {item_count} items."
        except Exception:
            reply = "✅ Catalog updated successfully."
        log_activity(seller_id, "ADD_VIA_WHATSAPP", raw_message)
    elif intent == "UPDATE":
        reply = "✅ Item updated successfully."
        log_activity(seller_id, "UPDATE_VIA_WHATSAPP", raw_message)
    elif intent == "DELETE":
        reply = "🗑️ Item removed from your catalog."
        log_activity(seller_id, "DELETE_VIA_WHATSAPP", raw_message)
    else:
        reply = "🤔 Sorry, I couldn't understand that. Try something like:\n• \"Add 10 kg atta at 450 rupees\"\n• \"Remove Maggi from my catalog\"\n• \"Update rice price to 60 rupees\""
        log_activity(seller_id, "UNKNOWN_INTENT", raw_message)
    
    # Send reply asynchronously targeting the original Twilio From formatting
    await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", reply) # type: ignore
    
    return {"status": "success", "processed_data": result, "reply_sent": reply}

# --- Catalog endpoints ---
@app.get("/api/catalog")
async def get_master_catalog(
    token: Optional[str] = Depends(get_jwt_token),
    limit: int = 50,
    offset: int = 0,
    seller_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
):
    """Endpoint for the dashboard to fetch the latest ONDC catalog."""
    if seller_id:
        catalogs = [get_catalog(seller_id, jwt_token=token)]
    else:
        catalogs = get_all_catalogs()
    
    all_items: List[Dict[str, Any]] = []
    for cat in catalogs:
        try:
            items = cat["bpp/catalog"]["bpp/providers"][0].get("items", [])
            all_items.extend(items)
        except (KeyError, IndexError):
            continue
            
    total_count = len(all_items)
    
    total_value: float = 0.0
    low_stock_count: int = 0
    for i in all_items:
        try:
            qty = float(i.get("quantity", {}).get("available", {}).get("count", 0))
            price = float(i.get("price", {}).get("value", 0))
            total_value += (price * qty) # type: ignore
            if qty < 5:
                low_stock_count += 1 # type: ignore
        except (ValueError, TypeError, AttributeError):
            pass
            
    paginated_items: List[Dict[str, Any]] = all_items[offset : offset + limit] # type: ignore
    
    # Feature 15: Search
    if search:
        search_lower = search.lower()
        paginated_items = [
            i for i in paginated_items
            if search_lower in str(i.get("descriptor", {}).get("name") or "").lower()
            or search_lower in str(i.get("category_id") or "").lower()
        ]
    
    # Feature 15: Sort
    if sort_by:
        reverse = sort_order.lower() == "desc"
        if sort_by == "name":
            paginated_items.sort(key=lambda x: str(x.get("descriptor", {}).get("name") or "").lower(), reverse=reverse)
        elif sort_by == "price":
            paginated_items.sort(key=lambda x: float(str(x.get("price", {}).get("value") or 0)), reverse=reverse)
        elif sort_by == "quantity":
            paginated_items.sort(key=lambda x: int(str(x.get("quantity", {}).get("available", {}).get("count") or 0)), reverse=reverse)
    
    return {
        "bpp/catalog": {
            "bpp/providers": [
                {
                    "id": "provider_master_merged",
                    "descriptor": {
                        "name": "ONDC Super Seller Network"
                    },
                    "items": paginated_items
                }
            ]
        },
        "pagination": {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "total_value": total_value,
            "low_stock_count": low_stock_count
        }
    }

# --- SSE Stream ---
@app.get("/api/catalog/stream")
async def catalog_stream(seller_id: Optional[str] = None, token: Optional[str] = Depends(get_jwt_token)):
    """Server-Sent Events endpoint for push-based catalog updates."""
    async def event_generator():
        last_hash = ""
        while True:
            try:
                if seller_id:
                    catalogs = [get_catalog(seller_id, jwt_token=token)]
                else:
                    catalogs = get_all_catalogs()
                
                all_items: list = []
                for cat in catalogs:
                    try:
                        items = cat["bpp/catalog"]["bpp/providers"][0].get("items", [])
                        all_items.extend(items)
                    except (KeyError, IndexError):
                        continue
                
                total_value: float = 0.0
                low_stock_count: int = 0
                for i in all_items:
                    try:
                        qty = float(i.get("quantity", {}).get("available", {}).get("count", 0))
                        price = float(i.get("price", {}).get("value", 0))
                        total_value += price * qty
                        if qty < 5:
                            low_stock_count += 1
                    except (ValueError, TypeError, AttributeError):
                        pass
                
                payload = json.dumps({
                    "items": all_items,
                    "total_count": len(all_items),
                    "total_value": total_value,
                    "low_stock_count": low_stock_count
                }, sort_keys=True)
                
                current_hash = str(hash(payload))
                if current_hash != last_hash:
                    last_hash = current_hash
                    yield f"data: {payload}\n\n"
                else:
                    yield f": heartbeat\n\n"
                    
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            
            await asyncio.sleep(2)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

# --- Sellers endpoint ---
@app.get("/api/sellers")
async def list_sellers(token: Optional[str] = Depends(get_jwt_token)):
    """Returns a list of all seller IDs known to the system."""
    seller_ids = get_all_seller_ids()
    return {"sellers": seller_ids}

# --- Activity Log ---
@app.get("/api/activity")
async def get_activity(limit: int = 50, seller_id: Optional[str] = None, token: Optional[str] = Depends(get_jwt_token)):
    """Returns recent activity log entries."""
    logs = get_activity_logs(limit=limit, seller_id=seller_id or "", jwt_token=token)
    return {"logs": logs}

# --- Analytics ---
@app.get("/api/analytics")
async def get_analytics(seller_id: Optional[str] = None, token: Optional[str] = Depends(get_jwt_token)):
    """Returns analytics data for the dashboard."""
    if seller_id:
        catalogs = [get_catalog(seller_id, jwt_token=token)]
    else:
        catalogs = get_all_catalogs()
    
    all_items: list = []
    for cat in catalogs:
        try:
            items = cat["bpp/catalog"]["bpp/providers"][0].get("items", [])
            all_items.extend(items)
        except (KeyError, IndexError):
            continue
    
    # Category breakdown
    categories: Dict[str, Any] = {}
    price_distribution: List[Dict[str, Any]] = []
    top_items: List[Dict[str, Any]] = []
    
    for item in all_items:
        try:
            name = item.get("descriptor", {}).get("name", "Unknown")
            cat_id = item.get("category_id", "Other")
            qty = float(item.get("quantity", {}).get("available", {}).get("count", 0))
            price = float(item.get("price", {}).get("value", 0))
            value = price * qty
            
            # Category aggregation
            if cat_id not in categories:
                categories[cat_id] = {"name": cat_id, "count": 0, "value": 0.0}
            categories[cat_id]["count"] += 1
            categories[cat_id]["value"] += value
            
            # Price distribution
            price_distribution.append({"name": name[:20], "price": price, "quantity": qty})
            
            # Top items by value
            top_items.append({"name": name, "value": value, "quantity": qty, "price": price})
        except (ValueError, TypeError, AttributeError):
            continue
    
    # Sort top items by value descending
    top_items.sort(key=lambda x: x["value"], reverse=True)
    
    # Stock status breakdown
    in_stock = sum(1 for i in all_items if float(i.get("quantity", {}).get("available", {}).get("count", 0)) >= 5)
    low_stock = sum(1 for i in all_items if 0 < float(i.get("quantity", {}).get("available", {}).get("count", 0)) < 5)
    out_of_stock = sum(1 for i in all_items if float(i.get("quantity", {}).get("available", {}).get("count", 0)) == 0)
    
    return {
        "total_products": len(all_items),
        "total_value": sum(i["value"] for i in top_items),
        "categories": list(categories.values()),
        "top_items": top_items[:10], # type: ignore
        "price_distribution": price_distribution[:20], # type: ignore
        "stock_status": [
            {"name": "In Stock", "value": in_stock, "fill": "#22c55e"},
            {"name": "Low Stock", "value": low_stock, "fill": "#eab308"},
            {"name": "Out of Stock", "value": out_of_stock, "fill": "#ef4444"},
        ]
    }

# --- CRUD with auth + activity logging ---
@app.post("/api/catalog/item", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def create_item(request: Request, item: ItemCreate, token: Optional[str] = Depends(get_jwt_token)):
    catalog = get_catalog(item.seller_id, jwt_token=token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError, TypeError):
        items = []

    new_item = {
        "id": str(uuid.uuid4()),
        "category_id": item.category_id,
        "descriptor": {
            "name": item.name,
            "short_desc": f"{item.quantity} {item.unit} of {item.name}"
        },
        "price": {
            "currency": "INR",
            "value": item.price
        },
        "quantity": {
            "available": {
                "count": item.quantity
            }
        }
    }
    items.append(new_item)
    
    if "bpp/catalog" not in catalog:
        catalog["bpp/catalog"] = {
            "bpp/providers": [{
                "id": f"provider_{item.seller_id}",
                "descriptor": {"name": f"Super Seller: {item.seller_id}"},
                "items": []
            }]
        }
        
    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = items
    save_catalog(item.seller_id, catalog, jwt_token=token)
    log_activity(item.seller_id, "ITEM_ADDED", item.name, f"Price: ₹{item.price}, Qty: {item.quantity} {item.unit}", jwt_token=token)
    return {"status": "success", "item": new_item, "message": f"Added {item.name} — ₹{item.price} × {item.quantity} {item.unit}"}

@app.put("/api/catalog/item/{item_id}", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def update_item(request: Request, item_id: str, item: ItemUpdate, token: Optional[str] = Depends(get_jwt_token)):
    catalog = get_catalog(item.seller_id, jwt_token=token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError, TypeError):
        return {"error": "Catalog not found"}

    for i in items:
        if isinstance(i, dict) and i.get("id") == item_id:
            if item.name is not None:
                if "descriptor" not in i: i["descriptor"] = {}
                i["descriptor"]["name"] = item.name
            if item.price is not None:
                if "price" not in i: i["price"] = {"currency": "INR", "value": "0"}
                i["price"]["value"] = item.price
            if item.quantity is not None:
                if "quantity" not in i: i["quantity"] = {"available": {"count": 0}}
                if "available" not in i["quantity"]: i["quantity"]["available"] = {"count": 0}
                i["quantity"]["available"]["count"] = item.quantity
                
            qty = i.get("quantity", {}).get("available", {}).get("count", 0)
            name = i.get("descriptor", {}).get("name", "Unknown")
            unit = item.unit if item.unit else "piece"
            
            if "descriptor" not in i: i["descriptor"] = {}
            i["descriptor"]["short_desc"] = f"{qty} {unit} of {name}"
            log_activity(item.seller_id, "ITEM_UPDATED", name, f"Price: ₹{item.price}, Qty: {item.quantity}", jwt_token=token)
            break
            
    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = items
    save_catalog(item.seller_id, catalog, jwt_token=token)
    return {"status": "success"}

@app.delete("/api/catalog/item/{item_id}", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def delete_item(request: Request, item_id: str, seller_id: str, token: Optional[str] = Depends(get_jwt_token)):
    from urllib.parse import unquote
    clean_seller_id = unquote(seller_id)
    catalog = get_catalog(clean_seller_id, jwt_token=token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError, TypeError):
        return {"error": "Catalog not found"}

    deleted_name = "Unknown"
    for i in items:
        if isinstance(i, dict) and i.get("id") == item_id:
            deleted_name = i.get("descriptor", {}).get("name", "Unknown")
            break

    updated_items = [i for i in items if isinstance(i, dict) and i.get("id") != item_id]
    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = updated_items
    save_catalog(clean_seller_id, catalog, jwt_token=token)
    log_activity(clean_seller_id, "ITEM_DELETED", deleted_name)
    return {"status": "success", "message": f"Removed {deleted_name} from your catalog"}

# --- Bulk delete ---
@app.post("/api/catalog/bulk-delete", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def bulk_delete_items(request: Request, req: BulkDeleteRequest, token: Optional[str] = Depends(get_jwt_token)):
    """Delete multiple items at once."""
    from urllib.parse import unquote
    clean_seller_id = unquote(req.seller_id)
    catalog = get_catalog(clean_seller_id, jwt_token=token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError, TypeError):
        return {"error": "Catalog not found"}

    ids_to_delete = set(req.item_ids)
    deleted_names = [i.get("descriptor", {}).get("name", "?") for i in items if isinstance(i, dict) and i.get("id") in ids_to_delete]
    updated_items = [i for i in items if isinstance(i, dict) and i.get("id") not in ids_to_delete]
    
    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = updated_items
    save_catalog(clean_seller_id, catalog, jwt_token=token)
    log_activity(clean_seller_id, "BULK_DELETE", ", ".join(deleted_names), f"Deleted {len(deleted_names)} items")
    return {"status": "success", "deleted_count": len(deleted_names)}

# --- Seller Profiles ---
@app.get("/api/seller/{seller_id}/profile")
async def get_profile(seller_id: str, token: Optional[str] = Depends(get_jwt_token)):
    """Get a seller's profile."""
    from urllib.parse import unquote
    profile = get_seller_profile(unquote(seller_id), jwt_token=token)
    return {"profile": profile}

@app.put("/api/seller/{seller_id}/profile", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def update_profile(request: Request, seller_id: str, profile: SellerProfileUpdate, token: Optional[str] = Depends(get_jwt_token)):
    """Update a seller's profile."""
    from urllib.parse import unquote
    clean_id = unquote(seller_id)
    existing = get_seller_profile(clean_id, jwt_token=token)
    updated = {
        "store_name": profile.store_name if profile.store_name is not None else existing.get("store_name", ""),
        "address": profile.address if profile.address is not None else existing.get("address", ""),
        "gst_number": profile.gst_number if profile.gst_number is not None else existing.get("gst_number", ""),
        "logo_url": profile.logo_url if profile.logo_url is not None else existing.get("logo_url", ""),
        "phone": profile.phone if profile.phone is not None else existing.get("phone", ""),
        "low_stock_alerts": profile.low_stock_alerts if profile.low_stock_alerts is not None else existing.get("low_stock_alerts", False),
    }
    save_seller_profile(clean_id, updated, jwt_token=token)
    log_activity(clean_id, "PROFILE_UPDATED", details=f"Store: {updated['store_name']}", jwt_token=token)
    return {"status": "success", "profile": get_seller_profile(clean_id, jwt_token=token)}

# --- Feature 14: Order Management ---
@app.post("/api/orders", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def place_order(request: Request, order: OrderCreate, token: Optional[str] = Depends(get_jwt_token)):
    """Create a new order and notify the seller via WhatsApp."""
    order_id = str(uuid.uuid4())
    order_data = {
        "id": order_id,
        "seller_id": order.seller_id,
        "buyer_name": order.buyer_name,
        "buyer_phone": order.buyer_phone,
        "items": order.items,
        "total_amount": order.total_amount,
        "status": "PLACED"
    }
    create_order(order_data, jwt_token=token)
    
    # Extract order_id substring cautiously to satiate Pyre slice infer errors
    short_id = order_id[:8] # type: ignore
    log_activity(order.seller_id, "ORDER_PLACED", details=f"Order {short_id} — ₹{order.total_amount}", jwt_token=token)
    
    # Notify seller via WhatsApp
    item_lines = "\n".join([f"  • {i.get('name', '?')} × {i.get('quantity', 1)}" for i in order.items])
    notification = (
        f"🛒 *New Order!*\n\n"
        f"From: {order.buyer_name or 'A customer'}\n"
        f"Items:\n{item_lines}\n\n"
        f"Total: ₹{order.total_amount}\n\n"
        f"Reply *accept* or *reject*."
    )
    await asyncio.to_thread(send_whatsapp_reply, order.seller_id, notification) # type: ignore
    
    return {"status": "success", "order_id": order_id}

@app.get("/api/orders")
async def list_orders(
    token: Optional[str] = Depends(get_jwt_token),
    seller_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None
):
    """List orders, optionally filtered by seller, status, dates, and search."""
    orders = get_orders(
        seller_id=seller_id or "",
        status=status or "",
        limit=limit,
        date_from=date_from or "",
        date_to=date_to or "",
        search=search or "",
        jwt_token=token
    )
    return {"orders": orders}

@app.put("/api/orders/{order_id}/status", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def change_order_status(request: Request, order_id: str, body: OrderStatusUpdate, token: Optional[str] = Depends(get_jwt_token)):
    """Update order status (PLACED → ACCEPTED → SHIPPED → DELIVERED or CANCELLED)."""
    valid_statuses = {"PLACED", "ACCEPTED", "SHIPPED", "DELIVERED", "CANCELLED"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    success = update_order_status(order_id, body.status, jwt_token=token)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")
    
    short_id = order_id[:8] # type: ignore
    log_activity("", f"ORDER_{body.status}", details=f"Order {short_id}", jwt_token=token)
    return {"status": "success", "order_status": body.status}

# --- Feature 17: Catalog Import ---
@app.post("/api/catalog/import", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def import_catalog(request: Request, data: CatalogImport, token: Optional[str] = Depends(get_jwt_token)):
    """Import items into a seller's catalog (merges with existing)."""
    from urllib.parse import unquote
    clean_seller_id = unquote(data.seller_id)
    catalog = get_catalog(clean_seller_id, jwt_token=token)
    
    existing_items: List[Dict[str, Any]] = []
    try:
        data_arr = catalog.get("bpp/catalog", {}).get("bpp/providers", [{}])[0].get("items", [])
        if isinstance(data_arr, list):
            existing_items = data_arr
    except (KeyError, IndexError, AttributeError):
        pass
    
    imported_count = 0
    for item in data.items:
        # Sanitize name
        clean_name = re.sub(r'<[^>]+>', '', item.name)
        clean_name = re.sub(r'[^\w\s\-]', '', clean_name).strip()
        if not clean_name:
            continue
        
        new_item = {
            "id": str(uuid.uuid4()),
            "descriptor": {"name": clean_name},
            "price": {"currency": "INR", "value": item.price},
            "quantity": {
                "available": {"count": item.quantity},
                "unitized": {"measure": {"unit": item.unit, "value": "1"}}
            },
            "category_id": item.category_id
        }
        existing_items.append(new_item)
        imported_count += 1
    
    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = existing_items
    save_catalog(clean_seller_id, catalog, jwt_token=token)
    log_activity(clean_seller_id, "CATALOG_IMPORTED", details=f"Imported {imported_count} items", jwt_token=token)
    
    return {"status": "success", "imported_count": imported_count, "total_items": len(existing_items)}

@app.post("/api/catalog/import/csv", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def import_csv(request: Request, seller_id: str = "", token: Optional[str] = Depends(get_jwt_token)):
    """Import catalog from CSV file upload (multipart/form-data)."""
    import csv
    import io
    from urllib.parse import unquote
    
    form = await request.form()
    file = form.get("file")
    seller = form.get("seller_id", seller_id)
    if not file or not seller:
        raise HTTPException(status_code=400, detail="Missing file or seller_id")
    
    clean_seller_id = unquote(str(seller))
    contents = await file.read()  # type: ignore
    text = contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    
    catalog = get_catalog(clean_seller_id, jwt_token=token)
    existing_items: List[Dict[str, Any]] = []
    try:
        data_arr = catalog.get("bpp/catalog", {}).get("bpp/providers", [{}])[0].get("items", [])
        if isinstance(data_arr, list):
            existing_items = data_arr
    except (KeyError, IndexError, AttributeError):
        pass
    
    imported_count = 0
    errors: List[str] = []
    for row_num, row in enumerate(reader, start=2):
        name = (row.get("name") or row.get("Name") or row.get("product_name") or "").strip()
        price = (row.get("price") or row.get("Price") or row.get("price_inr") or "0").strip()
        qty_str = (row.get("quantity") or row.get("Quantity") or row.get("qty") or "1").strip()
        unit = (row.get("unit") or row.get("Unit") or "piece").strip()
        category = (row.get("category") or row.get("Category") or row.get("category_id") or "Grocery").strip()
        
        if not name:
            errors.append(f"Row {row_num}: missing name")
            continue
        
        clean_name = re.sub(r'<[^>]+>', '', name)
        clean_name = re.sub(r'[^\w\s\-]', '', clean_name).strip()
        
        try:
            price_val = str(float(price))
            qty_val = int(float(qty_str))
        except ValueError:
            errors.append(f"Row {row_num}: invalid price/quantity")
            continue
        
        new_item = {
            "id": str(uuid.uuid4()),
            "descriptor": {"name": clean_name},
            "price": {"currency": "INR", "value": price_val},
            "quantity": {"available": {"count": qty_val}, "unitized": {"measure": {"unit": unit, "value": "1"}}},
            "category_id": category
        }
        existing_items.append(new_item)
        imported_count += 1
    
    if imported_count > 0:
        catalog["bpp/catalog"]["bpp/providers"][0]["items"] = existing_items
        save_catalog(clean_seller_id, catalog, jwt_token=token)
        log_activity(clean_seller_id, "CSV_IMPORTED", details=f"Imported {imported_count} items from CSV", jwt_token=token)
    
    return {
        "status": "success",
        "imported_count": imported_count,
        "total_items": len(existing_items),
        "errors": errors[:10]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# --- Feature 6: Low Stock Alert Background Task ---
async def check_low_stock_alerts():
    token = None
    """Background task that runs hourly, checks each seller's inventory,
    and sends WhatsApp alerts if low_stock_alerts is enabled."""
    while True:
        await asyncio.sleep(3600)  # every hour
        try:
            seller_ids = get_all_seller_ids()
            for sid in seller_ids:
                profile = get_seller_profile(sid)
                if not profile.get("low_stock_alerts"):
                    continue
                
                catalog = get_catalog(sid, jwt_token=token)
                try:
                    items = catalog.get("bpp/catalog", {}).get("bpp/providers", [{}])[0].get("items", [])
                except (KeyError, IndexError):
                    continue
                
                low_stock_items = []
                for item in items:
                    try:
                        qty = int(str(item.get("quantity", {}).get("available", {}).get("count", 0) or 0))
                        name = item.get("descriptor", {}).get("name", "Unknown")
                        if qty < 5:
                            low_stock_items.append(f"  \u2022 {name} ({qty} left)")
                    except (ValueError, TypeError):
                        continue
                
                if low_stock_items:
                    alert = (
                        f"\u26a0\ufe0f *Low Stock Alert*\n\n"
                        f"The following items are running low:\n"
                        + "\n".join(low_stock_items)
                        + "\n\n_Update stock via WhatsApp or dashboard._"
                    )
                    send_whatsapp_reply(sid, alert)
                    log_activity(sid, "LOW_STOCK_ALERT", details=f"{len(low_stock_items, jwt_token=token)} items low")
        except Exception:
            pass  # Never let the background task crash

