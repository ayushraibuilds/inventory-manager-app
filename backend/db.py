import os
import json
import time
import logging
from datetime import datetime
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv, dotenv_values

logger = logging.getLogger(__name__)

# --- Cached env loader ---
_env_cache = None
_env_cache_ts = 0
_ENV_TTL = 30  # seconds

def _get_env():
    global _env_cache, _env_cache_ts
    now = time.time()
    # Simple timestamp check - no locks to avoid async deadlocks under load
    if _env_cache is None or (now - _env_cache_ts > _ENV_TTL):
        # Merge: system env vars (Railway/Docker) + .env file (local dev)
        # .env file values take priority when both exist
        merged = dict(os.environ)
        merged.update(dotenv_values(".env"))
        _env_cache = merged
        _env_cache_ts = now
    return _env_cache


def get_supabase_client(jwt_token: str = None) -> Client:
    """
    Returns a Supabase client.
    If a user JWT is provided, requests will be authenticated as that user (respecting RLS).
    If no JWT is provided, falls back to the service_role key.
    """
    env_vars = _get_env()
    url = env_vars.get("SUPABASE_URL", "")
    anon = env_vars.get("SUPABASE_ANON_KEY", "")
    service = env_vars.get("SUPABASE_SERVICE_ROLE_KEY", "")

    # Dev bypass: treat mock token as unauthenticated (use service role)
    if jwt_token and jwt_token.startswith("dev-mock"):
        jwt_token = None
    
    if jwt_token:
        options = ClientOptions(headers={"Authorization": f"Bearer {jwt_token}"})
        return create_client(url, anon, options=options)
    else:
        return create_client(url, service)

# --- Empty Auth Stubs (Supabase Auth replaces custom auth) ---
def create_user(user_id: str, email: str, password_hash: str, seller_id: str):
    pass

def get_user_by_email(email: str) -> dict | None:
    pass

# --- Catalog (Products Table Mapping) ---
def build_empty_catalog():
    return {"bpp/catalog": {"bpp/providers": [{"items": []}]}}

def get_catalog(seller_id: str, jwt_token: str = None) -> dict:
    """Retrieve catalog products and format them as an ONDC Beckn catalog."""
    sb = get_supabase_client(jwt_token)
    try:
        response = sb.table("products").select("*").eq("seller_id", seller_id).execute()
    except Exception as e:
        logger.error(f"Supabase GET Error: {e}")
        return build_empty_catalog()
    
    catalog = build_empty_catalog()
    if response.data:
        items = []
        for row in response.data:
            items.append({
                "id": str(row["id"]),
                "descriptor": {"name": row["name"]},
                "price": {"value": str(row["price"]), "currency": "INR"},
                "quantity": {"available": {"count": row["quantity"]}},
                "category_id": row.get("category_id", "Grocery"),
                "unit": row.get("unit", "")
            })
        catalog["bpp/catalog"]["bpp/providers"][0]["items"] = items
        
    return catalog

def save_catalog(seller_id: str, catalog_json: dict, jwt_token: str = None):
    """Takes a full ONDC Beckn catalog and syncs it with the `products` table.
    Uses a granular diff: upserts changed/new items, deletes removed items.
    This preserves product UUIDs and avoids unnecessary DB churn."""
    ensure_profile_exists(seller_id, jwt_token)
    sb = get_supabase_client(jwt_token)
    
    try:
        items = catalog_json["bpp/catalog"]["bpp/providers"][0]["items"]
    except (KeyError, IndexError):
        items = []
    
    # Build the list of items to upsert
    new_ids = set()
    inserts = []
    for item in items:
        item_id = item.get("id")
        if item_id:
            new_ids.add(item_id)
        inserts.append({
            "id": item_id or str(__import__('uuid').uuid4()),
            "seller_id": seller_id,
            "name": item["descriptor"]["name"],
            "price": float(item["price"]["value"]),
            "quantity": int(item["quantity"]["available"]["count"]),
            "category_id": item.get("category_id", "Grocery"),
            "unit": item.get("unit", "")
        })
    
    try:
        # Fetch existing product IDs for this seller
        existing_resp = sb.table("products").select("id").eq("seller_id", seller_id).execute()
        existing_ids = {row["id"] for row in (existing_resp.data or [])}
        
        # Delete items that are no longer in the catalog
        ids_to_delete = existing_ids - new_ids
        if ids_to_delete:
            sb.table("products").delete().in_("id", list(ids_to_delete)).execute()
        
        # Upsert all current items (handles both inserts and updates)
        if inserts:
            sb.table("products").upsert(inserts).execute()
    except Exception as e:
        logger.error(f"Supabase save_catalog Error: {e}")

def get_all_catalogs() -> list:
    """Helper for the dashboard to quickly render everyone (Service Role used)."""
    sb = get_supabase_client()
    profiles_resp = sb.table("profiles").select("id").execute()
    catalogs = []
    for p in profiles_resp.data:
        catalogs.append(get_catalog(p["id"]))
    return catalogs

def get_all_seller_ids() -> list:
    """Returns a list of all seller IDs in the database."""
    sb = get_supabase_client()
    response = sb.table("profiles").select("id").execute()
    return [row["id"] for row in response.data] if response.data else []

# --- Activity Log ---
def log_activity(seller_id: str, action: str, item_name: str = "", details: str = "", jwt_token: str = None):
    ensure_profile_exists(seller_id, jwt_token)
    sb = get_supabase_client(jwt_token)
    try:
        sb.table("activity_log").insert({
            "seller_id": seller_id,
            "action": action,
            "item_name": item_name,
            "details": details
        }).execute()
    except Exception as e:
        logger.error(f"Supabase log_activity Error: {e}")

def get_activity_logs(limit: int = 50, seller_id: str = "", jwt_token: str = None) -> list:
    sb = get_supabase_client(jwt_token)
    query = sb.table("activity_log").select("*")
    if seller_id:
        query = query.eq("seller_id", seller_id)
    response = query.order("id", desc=True).limit(limit).execute()
    return response.data if response.data else []

def get_conversation_history(seller_id: str, limit: int = 3, jwt_token: str = None) -> list:
    """Retrieve the last N WhatsApp turns for a seller from the activity log.
    Returns [{role: "user"|"assistant", content: str}, ...]
    """
    sb = get_supabase_client(jwt_token)
    try:
        response = (
            sb.table("activity_log")
            .select("action, details")
            .eq("seller_id", seller_id)
            .in_("action", ["WHATSAPP_RECEIVED", "WHATSAPP_SENT"])
            .order("id", desc=True)
            .limit(limit * 2)  # fetch extra to ensure we get full turns
            .execute()
        )
        if not response.data:
            return []

        history = []
        for row in reversed(response.data):  # oldest first
            role = "user" if row["action"] == "WHATSAPP_RECEIVED" else "assistant"
            content = row.get("details", "")
            if content:
                history.append({"role": role, "content": content[:300]})  # cap length

        return history[-limit * 2:]  # at most limit pairs
    except Exception as e:
        logger.error(f"get_conversation_history error: {e}")
        return []


# --- Seller Profiles ---
def ensure_profile_exists(seller_id: str, jwt_token: str = None):
    sb = get_supabase_client(jwt_token)
    try:
        existing = sb.table("profiles").select("id").eq("id", seller_id).execute()
        if not existing.data:
            sb.table("profiles").insert({"id": seller_id, "user_id": seller_id}).execute()
    except Exception as e:
        logger.error(f"ensure_profile_exists error: {e}")

def get_seller_id_by_phone(phone: str, jwt_token: str = None) -> str:
    """Looks up a seller's UUID by their registered phone number."""
    sb = get_supabase_client(jwt_token)
    
    # Strip non-digits and use the last 10 for a broad LIKE match 
    # (handles +91 vs local formats resiliently)
    import re
    digits = re.sub(r"\D", "", phone)
    like_pattern = f"%{digits[-10:]}" if len(digits) >= 10 else phone

    try:
        response = sb.table("profiles").select("id").ilike("phone", like_pattern).execute()
        if response.data:
            return response.data[0]["id"]
    except Exception as e:
        logger.error(f"Phone lookup error: {e}")
    return None

def save_seller_profile(seller_id: str, profile: dict, jwt_token: str = None):
    sb = get_supabase_client(jwt_token)
    try:
        existing = sb.table("profiles").select("*").eq("id", seller_id).execute()
        current_data = existing.data[0] if existing.data else {"id": seller_id, "user_id": seller_id}
        
        for key, value in profile.items():
            current_data[key] = value
            
        current_data["updated_at"] = datetime.utcnow().isoformat()
        res = sb.table("profiles").upsert(current_data).execute()
        if hasattr(res, 'error') and res.error:
            logger.error(f"Supabase PostgREST error: {res.error}")
        else:
            logger.info(f"Profile upsert success: {current_data['id']}")
    except Exception as e:
        logger.error(f"Supabase upsert profile error: {e}")

def get_seller_profile(seller_id: str, jwt_token: str = None) -> dict:
    sb = get_supabase_client(jwt_token)
    response = sb.table("profiles").select("*").eq("id", seller_id).execute()
    if response.data:
        return response.data[0]
    return {
        "id": seller_id,
        "store_name": "",
        "address": "",
        "gst_number": "",
        "logo_url": "",
        "phone": "",
        "low_stock_alerts": False
    }

# --- Orders ---
def create_order(order: dict, jwt_token: str = None):
    sb = get_supabase_client(jwt_token)
    sb.table("orders").insert({
        "id": order["id"],
        "seller_id": order["seller_id"],
        "buyer_name": order.get("buyer_name", ""),
        "buyer_phone": order.get("buyer_phone", ""),
        "items_json": order.get("items", []),
        "total_amount": order.get("total_amount", 0),
        "status": order.get("status", "PLACED")
    }).execute()

def get_orders(seller_id: str = "", status: str = "", limit: int = 50, date_from: str = "", date_to: str = "", search: str = "", jwt_token: str = None) -> list:
    sb = get_supabase_client(jwt_token)
    query = sb.table("orders").select("*")
    if seller_id:
        query = query.eq("seller_id", seller_id)
    if status:
        query = query.eq("status", status)
    if date_from:
        query = query.gte("created_at", date_from)
    if date_to:
        query = query.lte("created_at", date_to + "T23:59:59")
    if search:
        query = query.or_(f"buyer_name.ilike.%{search}%,id.ilike.%{search}%")
        
    response = query.order("created_at", desc=True).limit(limit).execute()
    
    results = []
    if response.data:
        for row in response.data:
            row["items"] = row.get("items_json", [])
            row.pop("items_json", None)
            results.append(row)
    return results

def update_order_status(order_id: str, new_status: str, jwt_token: str = None) -> bool:
    sb = get_supabase_client(jwt_token)
    response = sb.table("orders").update({
        "status": new_status,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", order_id).execute()
    return len(response.data) > 0 if response.data else False
