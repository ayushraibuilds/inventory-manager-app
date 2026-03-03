"""Order management router — create, list, and update order status."""
import asyncio
import uuid
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from routes.auth import get_jwt_token, verify_api_key, send_whatsapp_reply
from db import create_order, get_orders, update_order_status, log_activity

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["orders"])          # /api/* — backward compat
v1_router = APIRouter(prefix="/api/v1", tags=["orders v1"])  # /api/v1/*


# --- Pydantic models ---
class OrderCreate(BaseModel):
    seller_id: str
    buyer_name: str = ""
    buyer_phone: str = ""
    items: List[Dict[str, Any]] = Field(default_factory=list)
    total_amount: float = 0


class OrderStatusUpdate(BaseModel):
    status: str = Field(
        description="One of: PLACED, ACCEPTED, SHIPPED, DELIVERED, CANCELLED"
    )


# --- Order endpoints ---
@router.post("/api/orders", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def place_order(
    request: Request,
    order: OrderCreate,
    token: Optional[str] = Depends(get_jwt_token),
):
    """Create a new order and notify the seller via WhatsApp."""
    order_id = str(uuid.uuid4())
    order_data = {
        "id": order_id,
        "seller_id": order.seller_id,
        "buyer_name": order.buyer_name,
        "buyer_phone": order.buyer_phone,
        "items": order.items,
        "total_amount": order.total_amount,
        "status": "PLACED",
    }
    create_order(order_data, jwt_token=token)

    short_id = order_id[:8]  # type: ignore
    log_activity(
        order.seller_id,
        "ORDER_PLACED",
        details=f"Order {short_id} — ₹{order.total_amount}",
        jwt_token=token,
    )

    # Notify seller via WhatsApp
    item_lines = "\n".join(
        [f"  • {i.get('name', '?')} × {i.get('quantity', 1)}" for i in order.items]
    )
    notification = (
        f"🛒 *New Order!*\n\n"
        f"From: {order.buyer_name or 'A customer'}\n"
        f"Items:\n{item_lines}\n\n"
        f"Total: ₹{order.total_amount}\n\n"
        f"Reply *accept* or *reject*."
    )
    await asyncio.to_thread(send_whatsapp_reply, order.seller_id, notification)  # type: ignore

    return {"status": "success", "order_id": order_id}


@router.get("/api/orders")
async def list_orders(
    token: Optional[str] = Depends(get_jwt_token),
    seller_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
):
    """List orders, optionally filtered by seller, status, dates, and search."""
    orders = get_orders(
        seller_id=seller_id or "",
        status=status or "",
        limit=limit,
        date_from=date_from or "",
        date_to=date_to or "",
        search=search or "",
        jwt_token=token,
    )
    return {"orders": orders}


@router.put("/api/orders/{order_id}/status", dependencies=[Depends(verify_api_key)])
@limiter.limit("60/minute")
async def change_order_status(
    request: Request,
    order_id: str,
    body: OrderStatusUpdate,
    token: Optional[str] = Depends(get_jwt_token),
):
    """Update order status (PLACED → ACCEPTED → SHIPPED → DELIVERED or CANCELLED)."""
    valid_statuses = {"PLACED", "ACCEPTED", "SHIPPED", "DELIVERED", "CANCELLED"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    success = update_order_status(order_id, body.status, jwt_token=token)
    if not success:
        raise HTTPException(status_code=404, detail="Order not found")

    short_id = order_id[:8]  # type: ignore
    log_activity(
        "", f"ORDER_{body.status}", details=f"Order {short_id}", jwt_token=token
    )
    return {"status": "success", "order_status": body.status}


# --- Register handlers on v1_router for /api/v1/* versioned paths ---
v1_router.post("/orders", dependencies=[Depends(verify_api_key)])(place_order)
v1_router.get("/orders")(list_orders)
v1_router.put("/orders/{order_id}/status", dependencies=[Depends(verify_api_key)])(change_order_status)
