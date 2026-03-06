"""Catalog CRUD, bulk operations, import, CSV import, SSE stream, analytics, and health check."""
import asyncio
import json
import os
import re
import uuid
import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from schemas import PaginatedCatalogResponse, PriceCheckResponse

from routes.auth import get_jwt_token, verify_api_key
from db import (
    get_all_catalogs,
    get_catalog,
    save_catalog,
    get_all_seller_ids,
    log_activity,
    get_activity_logs,
    get_seller_profile,
)

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["catalog"])          # /api/* — backward compat
v1_router = APIRouter(prefix="/api/v1", tags=["catalog v1"])  # /api/v1/*


# --- Pydantic models ---
class ItemCreate(BaseModel):
    name: str
    price: str
    quantity: int = Field(ge=0)
    unit: str
    seller_id: str
    category_id: str = "Grocery"

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        v = re.sub(r"<[^>]+>", "", v)
        v = re.sub(r"[^\w\s\-]", "", v)
        return v.strip()

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: str) -> str:
        try:
            if float(v) <= 0:
                raise ValueError("Price must be > 0")
        except ValueError:
            raise ValueError("Price must be a number > 0")
        return str(v)


class ItemUpdate(BaseModel):
    seller_id: str
    name: Optional[str] = None
    price: Optional[str] = None
    quantity: Optional[int] = Field(default=None, ge=0)
    unit: Optional[str] = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = re.sub(r"<[^>]+>", "", v)
        v = re.sub(r"[^\w\s\-]", "", v)
        return v.strip()

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            if float(v) <= 0:
                raise ValueError("Price must be > 0")
        except ValueError:
            raise ValueError("Price must be a number > 0")
        return str(v)


class BulkDeleteRequest(BaseModel):
    seller_id: str
    item_ids: List[str]


class CatalogImportItem(BaseModel):
    name: str
    price: str
    quantity: int = Field(ge=0)
    unit: str = "piece"
    category_id: str = "Grocery"


class CatalogImport(BaseModel):
    seller_id: str
    items: List[CatalogImportItem]


# --- Catalog Cache Helpers ---
async def invalidate_catalog_cache(seller_id: str):
    try:
        from redis_client import redis_client
        await redis_client.delete(f"catalog_db:{seller_id}")
        await redis_client.delete("catalog_db:all")
    except Exception as e:
        logger.warning(f"Redis invalidation skipped (likely offline): {e}")

# --- Catalog endpoints ---
@router.get("/api/catalog", response_model=PaginatedCatalogResponse)
@v1_router.get("/catalog", response_model=PaginatedCatalogResponse)
async def get_master_catalog(
    token: Optional[str] = Depends(get_jwt_token),
    limit: int = 50,
    offset: int = 0,
    seller_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
):
    """Endpoint for the dashboard to fetch the latest ONDC catalog."""
    cached = None
    cache_key = f"catalog_db:{seller_id}" if seller_id else "catalog_db:all"
    try:
        from redis_client import redis_client
        cached = await redis_client.get(cache_key)
    except Exception as e:
        logger.warning(f"Redis get skipped (likely offline): {e}")
        
    if cached:
        catalogs = json.loads(cached)
    else:
        if seller_id:
            catalogs = [await asyncio.to_thread(get_catalog, seller_id, jwt_token=token)]
        else:
            catalogs = await asyncio.to_thread(get_all_catalogs)
            
        try:
            from redis_client import redis_client
            await redis_client.set(cache_key, json.dumps(catalogs), ex=300)
        except Exception as e:
            logger.warning(f"Redis set skipped (likely offline): {e}")

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
            total_value += price * qty  # type: ignore
            if qty < 5:
                low_stock_count += 1  # type: ignore
        except (ValueError, TypeError, AttributeError):
            pass

    paginated_items: List[Dict[str, Any]] = all_items[offset : offset + limit]  # type: ignore

    # Search
    if search:
        search_lower = search.lower()
        paginated_items = [
            i
            for i in paginated_items
            if search_lower
            in str(i.get("descriptor", {}).get("name") or "").lower()
            or search_lower in str(i.get("category_id") or "").lower()
        ]

    # Sort
    if sort_by:
        reverse = sort_order.lower() == "desc"
        if sort_by == "name":
            paginated_items.sort(
                key=lambda x: str(
                    x.get("descriptor", {}).get("name") or ""
                ).lower(),
                reverse=reverse,
            )
        elif sort_by == "price":
            paginated_items.sort(
                key=lambda x: float(
                    str(x.get("price", {}).get("value") or 0)
                ),
                reverse=reverse,
            )
        elif sort_by == "quantity":
            paginated_items.sort(
                key=lambda x: int(
                    str(
                        x.get("quantity", {})
                        .get("available", {})
                        .get("count") or 0
                    )
                ),
                reverse=reverse,
            )

    return {
        "bpp/catalog": {
            "bpp/providers": [
                {
                    "id": "provider_master_merged",
                    "descriptor": {"name": "ONDC Super Seller Network"},
                    "items": paginated_items,
                }
            ]
        },
        "pagination": {
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "total_value": total_value,
            "low_stock_count": low_stock_count,
        },
    }


# --- SSE Stream ---
@router.get("/api/catalog/stream")
async def catalog_stream(
    seller_id: Optional[str] = None,
    token: Optional[str] = Depends(get_jwt_token),
):
    """Server-Sent Events endpoint for push-based catalog updates."""
    from fastapi.responses import StreamingResponse

    async def event_generator():
        last_hash = ""
        while True:
            try:
                if seller_id:
                    catalogs = [await asyncio.to_thread(get_catalog, seller_id, jwt_token=token)]
                else:
                    catalogs = await asyncio.to_thread(get_all_catalogs)

                all_items: list = []
                for cat in catalogs:
                    try:
                        items = cat["bpp/catalog"]["bpp/providers"][0].get(
                            "items", []
                        )
                        all_items.extend(items)
                    except (KeyError, IndexError):
                        continue

                total_value: float = 0.0
                low_stock_count: int = 0
                for i in all_items:
                    try:
                        qty = float(
                            i.get("quantity", {})
                            .get("available", {})
                            .get("count", 0)
                        )
                        price = float(i.get("price", {}).get("value", 0))
                        total_value += price * qty
                        if qty < 5:
                            low_stock_count += 1
                    except (ValueError, TypeError, AttributeError):
                        pass

                payload = json.dumps(
                    {
                        "items": all_items,
                        "total_count": len(all_items),
                        "total_value": total_value,
                        "low_stock_count": low_stock_count,
                    },
                    sort_keys=True,
                )

                current_hash = str(hash(payload))
                if current_hash != last_hash:
                    last_hash = current_hash
                    yield f"data: {payload}\n\n"
                else:
                    yield f": heartbeat\n\n"

            except Exception as e:
                yield f'data: {{"error": "{str(e)}"}}\n\n'

            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --- Sellers list ---
@router.get("/api/sellers")
async def list_sellers(token: Optional[str] = Depends(get_jwt_token)):
    """Returns a list of all seller IDs known to the system."""
    seller_ids = await asyncio.to_thread(get_all_seller_ids)
    return {"sellers": seller_ids}


# --- Activity Log ---
@router.get("/api/activity")
async def get_activity(
    limit: int = 50,
    seller_id: Optional[str] = None,
    token: Optional[str] = Depends(get_jwt_token),
):
    """Returns recent activity log entries."""
    logs = await asyncio.to_thread(get_activity_logs, limit=limit, seller_id=seller_id or "", jwt_token=token)
    return {"logs": logs}


# --- Analytics ---
@router.get("/api/analytics")
async def get_analytics(
    seller_id: Optional[str] = None,
    token: Optional[str] = Depends(get_jwt_token),
):
    """Returns analytics data for the dashboard."""
    if seller_id:
        catalogs = [await asyncio.to_thread(get_catalog, seller_id, jwt_token=token)]
    else:
        catalogs = await asyncio.to_thread(get_all_catalogs)

    all_items: list = []
    for cat in catalogs:
        try:
            items = cat["bpp/catalog"]["bpp/providers"][0].get("items", [])
            all_items.extend(items)
        except (KeyError, IndexError):
            continue

    categories: Dict[str, Any] = {}
    price_distribution: List[Dict[str, Any]] = []
    top_items: List[Dict[str, Any]] = []

    for item in all_items:
        try:
            name = item.get("descriptor", {}).get("name", "Unknown")
            cat_id = item.get("category_id", "Other")
            qty = float(
                item.get("quantity", {}).get("available", {}).get("count", 0)
            )
            price = float(item.get("price", {}).get("value", 0))
            value = price * qty

            if cat_id not in categories:
                categories[cat_id] = {"name": cat_id, "count": 0, "value": 0.0}
            categories[cat_id]["count"] += 1
            categories[cat_id]["value"] += value

            price_distribution.append(
                {"name": name[:20], "price": price, "quantity": qty}
            )
            top_items.append(
                {"name": name, "value": value, "quantity": qty, "price": price}
            )
        except (ValueError, TypeError, AttributeError):
            continue

    top_items.sort(key=lambda x: x["value"], reverse=True)

    in_stock = sum(
        1
        for i in all_items
        if float(i.get("quantity", {}).get("available", {}).get("count", 0)) >= 5
    )
    low_stock = sum(
        1
        for i in all_items
        if 0
        < float(i.get("quantity", {}).get("available", {}).get("count", 0))
        < 5
    )
    out_of_stock = sum(
        1
        for i in all_items
        if float(i.get("quantity", {}).get("available", {}).get("count", 0)) == 0
    )

    return {
        "total_products": len(all_items),
        "total_value": sum(i["value"] for i in top_items),
        "categories": list(categories.values()),
        "top_items": top_items[:10],  # type: ignore
        "price_distribution": price_distribution[:20],  # type: ignore
        "stock_status": [
            {"name": "In Stock", "value": in_stock, "fill": "#22c55e"},
            {"name": "Low Stock", "value": low_stock, "fill": "#eab308"},
            {"name": "Out of Stock", "value": out_of_stock, "fill": "#ef4444"},
        ],
    }


# --- CRUD with auth + activity logging ---
@router.post("/api/catalog/item", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def create_item(
    request: Request,
    item: ItemCreate,
    token: Optional[str] = Depends(get_jwt_token),
):
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
            "short_desc": f"{item.quantity} {item.unit} of {item.name}",
        },
        "price": {"currency": "INR", "value": item.price},
        "quantity": {"available": {"count": item.quantity}},
    }
    items.append(new_item)

    if "bpp/catalog" not in catalog:
        catalog["bpp/catalog"] = {
            "bpp/providers": [
                {
                    "id": f"provider_{item.seller_id}",
                    "descriptor": {"name": f"Super Seller: {item.seller_id}"},
                    "items": [],
                }
            ]
        }

    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = items
    save_catalog(item.seller_id, catalog, jwt_token=token)
    await invalidate_catalog_cache(item.seller_id)
    log_activity(
        item.seller_id,
        "ITEM_ADDED",
        item.name,
        f"Price: ₹{item.price}, Qty: {item.quantity} {item.unit}",
        jwt_token=token,
    )
    return {
        "status": "success",
        "item": new_item,
        "message": f"Added {item.name} — ₹{item.price} × {item.quantity} {item.unit}",
    }


@router.put("/api/catalog/item/{item_id}", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def update_item(
    request: Request,
    item_id: str,
    item: ItemUpdate,
    token: Optional[str] = Depends(get_jwt_token),
):
    catalog = get_catalog(item.seller_id, jwt_token=token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError, TypeError):
        return {"error": "Catalog not found"}

    for i in items:
        if isinstance(i, dict) and i.get("id") == item_id:
            if item.name is not None:
                if "descriptor" not in i:
                    i["descriptor"] = {}
                i["descriptor"]["name"] = item.name
            if item.price is not None:
                if "price" not in i:
                    i["price"] = {"currency": "INR", "value": "0"}
                i["price"]["value"] = item.price
            if item.quantity is not None:
                if "quantity" not in i:
                    i["quantity"] = {"available": {"count": 0}}
                if "available" not in i["quantity"]:
                    i["quantity"]["available"] = {"count": 0}
                i["quantity"]["available"]["count"] = item.quantity

            qty = i.get("quantity", {}).get("available", {}).get("count", 0)
            name = i.get("descriptor", {}).get("name", "Unknown")
            unit = item.unit if item.unit else "piece"

            if "descriptor" not in i:
                i["descriptor"] = {}
            i["descriptor"]["short_desc"] = f"{qty} {unit} of {name}"
            log_activity(
                item.seller_id,
                "ITEM_UPDATED",
                name,
                f"Price: ₹{item.price}, Qty: {item.quantity}",
                jwt_token=token,
            )
            break

    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = items
    save_catalog(item.seller_id, catalog, jwt_token=token)
    await invalidate_catalog_cache(item.seller_id)
    return {"status": "success"}


@router.delete("/api/catalog/item/{item_id}", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def delete_item(
    request: Request,
    item_id: str,
    seller_id: str,
    token: Optional[str] = Depends(get_jwt_token),
):
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

    updated_items = [
        i for i in items if isinstance(i, dict) and i.get("id") != item_id
    ]
    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = updated_items
    save_catalog(clean_seller_id, catalog, jwt_token=token)
    await invalidate_catalog_cache(clean_seller_id)
    log_activity(clean_seller_id, "ITEM_DELETED", deleted_name)
    return {
        "status": "success",
        "message": f"Removed {deleted_name} from your catalog",
    }


# --- Bulk delete ---
@router.post("/api/catalog/bulk-delete", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def bulk_delete_items(
    request: Request,
    req: BulkDeleteRequest,
    token: Optional[str] = Depends(get_jwt_token),
):
    """Delete multiple items at once."""
    from urllib.parse import unquote

    clean_seller_id = unquote(req.seller_id)
    catalog = get_catalog(clean_seller_id, jwt_token=token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError, TypeError):
        return {"error": "Catalog not found"}

    ids_to_delete = set(req.item_ids)
    deleted_names = [
        i.get("descriptor", {}).get("name", "?")
        for i in items
        if isinstance(i, dict) and i.get("id") in ids_to_delete
    ]
    updated_items = [
        i
        for i in items
        if isinstance(i, dict) and i.get("id") not in ids_to_delete
    ]

    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = updated_items
    save_catalog(clean_seller_id, catalog, jwt_token=token)
    await invalidate_catalog_cache(clean_seller_id)
    log_activity(
        clean_seller_id,
        "BULK_DELETE",
        ", ".join(deleted_names),
        f"Deleted {len(deleted_names)} items",
    )
    return {"status": "success", "deleted_count": len(deleted_names)}


# --- Catalog Import ---
@router.post("/api/catalog/import", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def import_catalog(
    request: Request,
    data: CatalogImport,
    token: Optional[str] = Depends(get_jwt_token),
):
    """Import items into a seller's catalog (merges with existing)."""
    from urllib.parse import unquote

    clean_seller_id = unquote(data.seller_id)
    catalog = get_catalog(clean_seller_id, jwt_token=token)

    existing_items: List[Dict[str, Any]] = []
    try:
        data_arr = (
            catalog.get("bpp/catalog", {})
            .get("bpp/providers", [{}])[0]
            .get("items", [])
        )
        if isinstance(data_arr, list):
            existing_items = data_arr
    except (KeyError, IndexError, AttributeError):
        pass

    imported_count = 0
    for item in data.items:
        clean_name = re.sub(r"<[^>]+>", "", item.name)
        clean_name = re.sub(r"[^\w\s\-]", "", clean_name).strip()
        if not clean_name:
            continue

        new_item = {
            "id": str(uuid.uuid4()),
            "descriptor": {"name": clean_name},
            "price": {"currency": "INR", "value": item.price},
            "quantity": {
                "available": {"count": item.quantity},
                "unitized": {"measure": {"unit": item.unit, "value": "1"}},
            },
            "category_id": item.category_id,
        }
        existing_items.append(new_item)
        imported_count += 1

    catalog["bpp/catalog"]["bpp/providers"][0]["items"] = existing_items
    save_catalog(clean_seller_id, catalog, jwt_token=token)
    await invalidate_catalog_cache(clean_seller_id)
    log_activity(
        clean_seller_id,
        "CATALOG_IMPORTED",
        details=f"Imported {imported_count} items",
        jwt_token=token,
    )

    return {
        "status": "success",
        "imported_count": imported_count,
        "total_items": len(existing_items),
    }


@router.post("/api/catalog/import/csv", dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def import_csv(
    request: Request,
    seller_id: str = "",
    token: Optional[str] = Depends(get_jwt_token),
):
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
        data_arr = (
            catalog.get("bpp/catalog", {})
            .get("bpp/providers", [{}])[0]
            .get("items", [])
        )
        if isinstance(data_arr, list):
            existing_items = data_arr
    except (KeyError, IndexError, AttributeError):
        pass

    imported_count = 0
    errors: List[str] = []
    for row_num, row in enumerate(reader, start=2):
        name = (
            row.get("name") or row.get("Name") or row.get("product_name") or ""
        ).strip()
        price = (
            row.get("price") or row.get("Price") or row.get("price_inr") or "0"
        ).strip()
        qty_str = (
            row.get("quantity") or row.get("Quantity") or row.get("qty") or "1"
        ).strip()
        unit = (row.get("unit") or row.get("Unit") or "piece").strip()
        category = (
            row.get("category")
            or row.get("Category")
            or row.get("category_id")
            or "Grocery"
        ).strip()

        if not name:
            errors.append(f"Row {row_num}: missing name")
            continue

        clean_name = re.sub(r"<[^>]+>", "", name)
        clean_name = re.sub(r"[^\w\s\-]", "", clean_name).strip()

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
            "quantity": {
                "available": {"count": qty_val},
                "unitized": {"measure": {"unit": unit, "value": "1"}},
            },
            "category_id": category,
        }
        existing_items.append(new_item)
        imported_count += 1

    if imported_count > 0:
        catalog["bpp/catalog"]["bpp/providers"][0]["items"] = existing_items
        save_catalog(clean_seller_id, catalog, jwt_token=token)
        await invalidate_catalog_cache(clean_seller_id)
        log_activity(
            clean_seller_id,
            "CSV_IMPORTED",
            details=f"Imported {imported_count} items from CSV",
            jwt_token=token,
        )

    return {
        "status": "success",
        "imported_count": imported_count,
        "total_items": len(existing_items),
        "errors": errors[:10],
    }


# --- Enriched Health Check ---
@router.get("/health")
@v1_router.get("/health")
async def health_check():
    """Returns service health with dependency status."""
    result: Dict[str, Any] = {
        "status": "healthy",
        "supabase": "unknown",
        "llm": "unknown",
        "twilio": "unknown",
    }

    # Check Supabase
    try:
        from db import get_supabase_client
        sb = get_supabase_client()
        sb.table("profiles").select("id").limit(1).execute()
        result["supabase"] = "ok"
    except Exception as e:
        result["supabase"] = f"error: {str(e)[:80]}"
        result["status"] = "degraded"

    # Check Groq LLM
    try:
        from langchain_groq import ChatGroq
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        llm.invoke("ping")
        result["llm"] = "ok"
    except Exception as e:
        result["llm"] = f"error: {str(e)[:80]}"
        result["status"] = "degraded"

    # Check Twilio
    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    if not twilio_sid or not twilio_token:
        result["twilio"] = "not_configured"
    else:
        try:
            from twilio.rest import Client
            client = Client(twilio_sid, twilio_token)
            client.api.accounts(twilio_sid).fetch()
            result["twilio"] = "ok"
        except Exception as e:
            result["twilio"] = f"error: {str(e)[:80]}"
            result["status"] = "degraded"

    return result


@router.get("/catalog/price-check")
async def price_check_catalog(seller_id: str, token: str = Depends(get_jwt_token)):
    """Return price intelligence for all items in a seller's catalog."""
    from price_reference import get_catalog_price_report

    catalog = get_catalog(seller_id, token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError):
        items = []

    if not items:
        return {"seller_id": seller_id, "total_items": 0, "suggestions": []}

    suggestions = get_catalog_price_report(items)

    return {
        "seller_id": seller_id,
        "total_items": len(items),
        "items_with_suggestions": len(suggestions),
        "suggestions": suggestions,
    }


# --- CSV Export ---

@router.get("/api/catalog/export/csv")
async def export_catalog_csv(seller_id: str, token: str = Depends(get_jwt_token)):
    """Export the full catalog as a downloadable CSV file."""
    import csv
    import io
    from fastapi.responses import StreamingResponse

    catalog = get_catalog(seller_id, token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError):
        items = []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Price (INR)", "Quantity", "Unit", "Category"])

    for item in items:
        desc = item.get("descriptor", {})
        price = item.get("price", {})
        qty = item.get("quantity", {}).get("available", {}).get("count", 0)
        unit = ""
        if desc.get("short_desc"):
            parts = desc["short_desc"].split(" ")
            if len(parts) > 1:
                unit = parts[1]
        writer.writerow([
            desc.get("name", "Unknown"),
            price.get("value", "0"),
            qty,
            unit or "piece",
            item.get("category_id", "Grocery"),
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="catalog_{seller_id[:8]}.csv"'},
    )


# --- Batch Price Update ---

class BatchPriceItem(BaseModel):
    item_id: str
    new_price: str


class BatchPriceUpdate(BaseModel):
    seller_id: str
    updates: List[BatchPriceItem]


@router.post("/api/catalog/batch-price-update")
@limiter.limit("10/minute")
async def batch_price_update(request: Request, data: BatchPriceUpdate, token: str = Depends(get_jwt_token)):
    """Update prices for multiple items at once (e.g. match market prices)."""
    catalog = get_catalog(data.seller_id, jwt_token=token)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=404, detail="Catalog not found")

    # Build lookup of price updates
    price_map = {}
    for u in data.updates:
        price_val = re.sub(r"[^0-9.]", "", str(u.new_price))
        if price_val and float(price_val) > 0:
            price_map[u.item_id] = price_val

    updated = 0
    for item in items:
        if isinstance(item, dict) and item.get("id") in price_map:
            if "price" not in item:
                item["price"] = {"currency": "INR", "value": "0"}
            item["price"]["value"] = price_map[item["id"]]
            updated += 1

    if updated > 0:
        catalog["bpp/catalog"]["bpp/providers"][0]["items"] = items
        save_catalog(data.seller_id, catalog, jwt_token=token)
        log_activity(
            data.seller_id,
            "BATCH_PRICE_UPDATE",
            f"{updated} items",
            f"Updated {updated} prices to market rates",
            jwt_token=token,
        )

    return {
        "updated": updated,
        "total_requested": len(data.updates),
    }


# --- Register all route handler functions on v1_router as well ---
# We bind each handler directly to both /api/* and /api/v1/* by re-using
# the same async function with v1_router decorators.

v1_router.get("/catalog")(get_master_catalog)
v1_router.get("/catalog/stream")(catalog_stream)
v1_router.get("/sellers")(list_sellers)
v1_router.get("/activity")(get_activity)
v1_router.get("/analytics")(get_analytics)
v1_router.get("/catalog/price-check")(price_check_catalog)
v1_router.get("/catalog/export/csv")(export_catalog_csv)
v1_router.post("/catalog/batch-price-update")(batch_price_update)
v1_router.post("/catalog/item", dependencies=[Depends(verify_api_key)])(create_item)
v1_router.put("/catalog/item/{item_id}", dependencies=[Depends(verify_api_key)])(update_item)
v1_router.delete("/catalog/item/{item_id}", dependencies=[Depends(verify_api_key)])(delete_item)
v1_router.post("/catalog/bulk-delete", dependencies=[Depends(verify_api_key)])(bulk_delete_items)
v1_router.post("/catalog/import", dependencies=[Depends(verify_api_key)])(import_catalog)
v1_router.post("/catalog/import/csv", dependencies=[Depends(verify_api_key)])(import_csv)
