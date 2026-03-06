"""Seller profile router — get/update profiles, phone linking."""
import asyncio
from typing import Optional

from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from schemas import SellerProfileResponse, SellerProfileUpdateResponse
from routes.auth import get_jwt_token, send_whatsapp_reply
from db import save_seller_profile, get_seller_profile, log_activity

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["sellers"])          # /api/* — backward compat
v1_router = APIRouter(prefix="/api/v1", tags=["sellers v1"])  # /api/v1/*


class SellerProfileUpdate(BaseModel):
    store_name: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    logo_url: Optional[str] = None
    phone: Optional[str] = None
    low_stock_alerts: Optional[bool] = None


@router.get("/api/seller/{seller_id}/profile", response_model=SellerProfileResponse)
async def get_profile(
    seller_id: str, token: Optional[str] = Depends(get_jwt_token)
):
    """Get a seller's profile."""
    from urllib.parse import unquote

    profile = get_seller_profile(unquote(seller_id), jwt_token=token)
    return {"profile": profile}


@router.put("/api/seller/{seller_id}/profile", response_model=SellerProfileUpdateResponse)
@limiter.limit("30/minute")
async def update_profile(
    request: Request,
    seller_id: str,
    profile: SellerProfileUpdate,
    token: Optional[str] = Depends(get_jwt_token),
):
    """Update a seller's profile."""
    from urllib.parse import unquote

    clean_id = unquote(seller_id)
    existing = get_seller_profile(clean_id, jwt_token=token)
    updated = {
        "store_name": profile.store_name
        if profile.store_name is not None
        else existing.get("store_name", ""),
        "address": profile.address
        if profile.address is not None
        else existing.get("address", ""),
        "gst_number": profile.gst_number
        if profile.gst_number is not None
        else existing.get("gst_number", ""),
        "logo_url": profile.logo_url
        if profile.logo_url is not None
        else existing.get("logo_url", ""),
        "phone": str(profile.phone).replace(" ", "").replace("-", "")
        if profile.phone is not None
        else existing.get("phone", ""),
        "low_stock_alerts": profile.low_stock_alerts
        if profile.low_stock_alerts is not None
        else existing.get("low_stock_alerts", False),
    }
    save_seller_profile(clean_id, updated, jwt_token=token)
    log_activity(
        clean_id,
        "PROFILE_UPDATED",
        details=f"Store: {updated['store_name']}",
        jwt_token=token,
    )

    # Trigger a WhatsApp welcome message if phone was just added or changed
    if updated.get("phone") and updated.get("phone") != existing.get("phone"):
        welcome_msg = (
            f"🎉 *Welcome to ONDC Super Seller, {updated['store_name']}!*\n\n"
            "Your account is successfully linked! You can now manage your catalog right from WhatsApp using AI.\n\n"
            "Try replying with:\n"
            '• "Add 10 kg atta for 450 rupees"\n'
            '• "Remove Maggi"\n'
            '• "Update rice price to 60 rupees"'
        )
        await asyncio.to_thread(
            send_whatsapp_reply, f"whatsapp:{updated['phone']}", welcome_msg
        )  # type: ignore

    return {
        "status": "success",
        "profile": get_seller_profile(clean_id, jwt_token=token),
    }


# --- Register handlers on v1_router for /api/v1/* versioned paths ---
v1_router.get("/seller/{seller_id}/profile")(get_profile)
v1_router.put("/seller/{seller_id}/profile")(update_profile)
