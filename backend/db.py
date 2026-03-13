import os
import json
import logging
from datetime import datetime, timedelta
from supabase import create_client, Client, ClientOptions
from env_utils import get_merged_env

logger = logging.getLogger(__name__)


def _default_trial_fields() -> dict:
    now = datetime.utcnow()
    trial_end = now + timedelta(days=7)
    return {
        "billing_plan": "pro",
        "billing_status": "trialing",
        "billing_interval": "trial",
        "billing_provider": "trial",
        "plan_started_at": now.isoformat(),
        "current_period_start": now.isoformat(),
        "current_period_end": trial_end.isoformat(),
        "trial_started_at": now.isoformat(),
        "trial_ends_at": trial_end.isoformat(),
    }

def _get_env():
    return get_merged_env()


def get_supabase_client(jwt_token: str = None, use_service_role: bool = False) -> Client:
    """
    Returns a Supabase client.
    If a user JWT is provided, requests will be authenticated as that user (respecting RLS).
    If no JWT is provided, it uses the anon key unless service_role access is explicitly requested.
    """
    env_vars = _get_env()
    url = env_vars.get("SUPABASE_URL", "")
    anon = env_vars.get("SUPABASE_ANON_KEY", "")
    service = env_vars.get("SUPABASE_SERVICE_ROLE_KEY", "")

    # Dev bypass: treat mock token as unauthenticated (use service role)
    if jwt_token == "service-role-api-key":
        jwt_token = None
        use_service_role = True

    if jwt_token and jwt_token.startswith("dev-mock"):
        jwt_token = None

    if jwt_token:
        options = ClientOptions(headers={"Authorization": f"Bearer {jwt_token}"})
        return create_client(url, anon, options=options)
    if use_service_role:
        return create_client(url, service)
    return create_client(url, anon)


def _extract_item_metadata(item: dict) -> tuple[str, str, list[str]]:
    descriptor = item.get("descriptor", {})
    quantity = item.get("quantity", {})

    short_desc = ""
    images: list[str] = []
    if isinstance(descriptor, dict):
        short_desc = str(descriptor.get("short_desc", "") or "")
        raw_images = descriptor.get("images", [])
        if isinstance(raw_images, list):
            images = [str(img) for img in raw_images if img]

    unit = str(item.get("unit", "") or "")
    if not unit and isinstance(quantity, dict):
        unitized = quantity.get("unitized", {})
        if isinstance(unitized, dict):
            measure = unitized.get("measure", {})
            if isinstance(measure, dict):
                unit = str(measure.get("unit", "") or "")

    if not unit and short_desc:
        parts = short_desc.split(" ")
        if len(parts) > 1:
            unit = parts[1]

    return unit, short_desc, images


def _pack_unit_metadata(item: dict) -> str:
    unit, short_desc, images = _extract_item_metadata(item)
    payload = {"unit": unit}
    if short_desc:
        payload["short_desc"] = short_desc
    if images:
        payload["images"] = images
    return json.dumps(payload, separators=(",", ":"))


def _unpack_unit_metadata(raw_value: str | None) -> tuple[str, str, list[str]]:
    if not raw_value:
        return "", "", []

    if isinstance(raw_value, str):
        try:
            decoded = json.loads(raw_value)
        except json.JSONDecodeError:
            return raw_value, "", []
        if isinstance(decoded, dict):
            unit = str(decoded.get("unit", "") or "")
            short_desc = str(decoded.get("short_desc", "") or "")
            raw_images = decoded.get("images", [])
            images = [str(img) for img in raw_images] if isinstance(raw_images, list) else []
            return unit, short_desc, images

    return str(raw_value), "", []

# --- Empty Auth Stubs (Supabase Auth replaces custom auth) ---
def create_user(user_id: str, email: str, password_hash: str, seller_id: str):
    pass

def get_user_by_email(email: str) -> dict | None:
    pass

# --- Catalog (Products Table Mapping) ---
def build_empty_catalog():
    return {"bpp/catalog": {"bpp/providers": [{"items": []}]}}

def get_catalog(seller_id: str, jwt_token: str = None, service_role: bool = False) -> dict:
    """Retrieve catalog products and format them as an ONDC Beckn catalog."""
    sb = get_supabase_client(jwt_token, use_service_role=service_role)
    try:
        response = sb.table("products").select("*").eq("seller_id", seller_id).execute()
    except Exception as e:
        logger.error(f"Supabase GET Error: {e}")
        return build_empty_catalog()
    
    catalog = build_empty_catalog()
    if response.data:
        items = []
        for row in response.data:
            unit, short_desc, images = _unpack_unit_metadata(row.get("unit", ""))
            descriptor = {"name": row["name"]}
            if short_desc:
                descriptor["short_desc"] = short_desc
            if images:
                descriptor["images"] = images
            items.append({
                "id": str(row["id"]),
                "descriptor": descriptor,
                "price": {"value": str(row["price"]), "currency": "INR"},
                "quantity": {"available": {"count": row["quantity"]}},
                "category_id": row.get("category_id", "Grocery"),
                "unit": unit
            })
        catalog["bpp/catalog"]["bpp/providers"][0]["items"] = items
        
    return catalog

def save_catalog(seller_id: str, catalog_json: dict, jwt_token: str = None, service_role: bool = False) -> bool:
    """Takes a full ONDC Beckn catalog and syncs it with the `products` table.
    Uses a granular diff: upserts changed/new items, deletes removed items.
    This preserves product UUIDs and avoids unnecessary DB churn."""
    ensure_profile_exists(seller_id, jwt_token, service_role=service_role)
    sb = get_supabase_client(jwt_token, use_service_role=service_role)
    
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
            "unit": _pack_unit_metadata(item)
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
        return True
    except Exception as e:
        logger.error(f"Supabase save_catalog Error: {e}")
        return False

def get_all_catalogs() -> list:
    """Helper for the dashboard to quickly render everyone (Service Role used)."""
    sb = get_supabase_client(use_service_role=True)
    profiles_resp = sb.table("profiles").select("id").execute()
    catalogs = []
    for p in profiles_resp.data:
        catalogs.append(get_catalog(p["id"], service_role=True))
    return catalogs

def get_all_seller_ids() -> list:
    """Returns a list of all seller IDs in the database."""
    sb = get_supabase_client(use_service_role=True)
    response = sb.table("profiles").select("id").execute()
    return [row["id"] for row in response.data] if response.data else []

# --- Activity Log ---
def log_activity(
    seller_id: str,
    action: str,
    item_name: str = "",
    details: str = "",
    jwt_token: str = None,
    service_role: bool = False,
):
    if seller_id:
        ensure_profile_exists(seller_id, jwt_token, service_role=service_role)
    sb = get_supabase_client(jwt_token, use_service_role=service_role)
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
    sb = get_supabase_client(jwt_token, use_service_role=jwt_token is None)
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
def ensure_profile_exists(seller_id: str, jwt_token: str = None, service_role: bool = False):
    if not seller_id:
        return
    sb = get_supabase_client(jwt_token, use_service_role=service_role)
    try:
        existing = sb.table("profiles").select("id").eq("id", seller_id).execute()
        if not existing.data:
            sb.table("profiles").insert({
                "id": seller_id,
                "user_id": seller_id,
                **_default_trial_fields(),
            }).execute()
    except Exception as e:
        logger.error(f"ensure_profile_exists error: {e}")

def get_seller_id_by_phone(phone: str, jwt_token: str = None) -> str:
    """Looks up a seller's UUID by their registered phone number."""
    sb = get_supabase_client(jwt_token, use_service_role=jwt_token is None)
    
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
        current_data = existing.data[0] if existing.data else {
            "id": seller_id,
            "user_id": seller_id,
            **_default_trial_fields(),
        }
        
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
    sb = get_supabase_client(jwt_token, use_service_role=jwt_token is None)
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
        "low_stock_alerts": False,
        "billing_plan": "free",
        "billing_status": "trialing",
        "billing_interval": "trial",
        "billing_provider": "trial",
        "billing_email": "",
        "razorpay_customer_id": "",
        "razorpay_subscription_id": "",
        "plan_started_at": _default_trial_fields()["plan_started_at"],
        "current_period_start": _default_trial_fields()["current_period_start"],
        "current_period_end": _default_trial_fields()["current_period_end"],
        "trial_started_at": _default_trial_fields()["trial_started_at"],
        "trial_ends_at": _default_trial_fields()["trial_ends_at"],
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
