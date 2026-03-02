import os
import json
from datetime import datetime
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv

from dotenv import dotenv_values

def get_supabase_client(jwt_token: str = None) -> Client:
    """
    Returns a Supabase client.
    If a user JWT is provided, requests will be authenticated as that user (respecting RLS).
    If no JWT is provided, falls back to the service_role key.
    """
    # Dynamically read `.env` bypassing static os.environ cache during hot-reloads
    env_vars = dotenv_values(".env")
    url = env_vars.get("SUPABASE_URL", "")
    anon = env_vars.get("SUPABASE_ANON_KEY", "")
    service = env_vars.get("SUPABASE_SERVICE_ROLE_KEY", "")
    
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
        print(f"Supabase GET Error: {e}")
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
    """Takes a full ONDC Beckn catalog and syncs it with the `products` table."""
    ensure_profile_exists(seller_id, jwt_token)
    sb = get_supabase_client(jwt_token)
    
    try:
        items = catalog_json["bpp/catalog"]["bpp/providers"][0]["items"]
    except (KeyError, IndexError):
        items = []
    
    # We will delete all current products for this seller and insert the new ones.
    # Note: A real production system might prefer fine-grained upserts without deleting,
    # but since the agent manipulates the entire JSON array, full sync is safest.
    try:
        sb.table("products").delete().eq("seller_id", seller_id).execute()
        
        if items:
            inserts = []
            for item in items:
                inserts.append({
                    "id": item.get("id"),
                    "seller_id": seller_id,
                    "name": item["descriptor"]["name"],
                    "price": float(item["price"]["value"]),
                    "quantity": int(item["quantity"]["available"]["count"]),
                    "category_id": item.get("category_id", "Grocery"),
                    "unit": item.get("unit", "")
                })
            sb.table("products").upsert(inserts).execute()
    except Exception as e:
        print(f"Supabase save_catalog Error: {e}")

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
        print(f"Supabase log_activity Error: {e}")

def get_activity_logs(limit: int = 50, seller_id: str = "", jwt_token: str = None) -> list:
    sb = get_supabase_client(jwt_token)
    query = sb.table("activity_log").select("*")
    if seller_id:
        query = query.eq("seller_id", seller_id)
    response = query.order("id", desc=True).limit(limit).execute()
    return response.data if response.data else []

# --- Seller Profiles ---
def ensure_profile_exists(seller_id: str, jwt_token: str = None):
    sb = get_supabase_client(jwt_token)
    try:
        existing = sb.table("profiles").select("id").eq("id", seller_id).execute()
        if not existing.data:
            sb.table("profiles").insert({"id": seller_id, "user_id": seller_id}).execute()
    except Exception as e:
        print(f"ensure_profile_exists error: {e}")

def get_seller_id_by_phone(phone: str, jwt_token: str = None) -> str:
    """Looks up a seller's UUID by their registered phone number."""
    sb = get_supabase_client(jwt_token)
    try:
        response = sb.table("profiles").select("id").eq("phone", phone).execute()
        if response.data:
            return response.data[0]["id"]
    except Exception as e:
        print(f"Phone lookup error: {e}")
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
            print(f"SUPABASE POSTGREST ERROR: {res.error}")
        else:
            print(f"PROFILE UPSERT SUCCESS: {current_data['id']}")
    except Exception as e:
        print(f"Supabase upsert profile Exception: {e}")

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
