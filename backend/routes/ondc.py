"""ONDC Network Integration Routes — sandbox endpoints for Beckn protocol."""
import logging
import re
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional

from slowapi import Limiter
from slowapi.util import get_remote_address

from db import get_catalog, get_seller_profile, get_all_seller_ids
from ondc_adapter import build_on_search_response, BPP_ID, BPP_URI

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1/ondc", tags=["ONDC"])


class SearchRequest(BaseModel):
    """Simplified search request (mimics ONDC /search)."""
    context: Optional[dict] = None
    message: Optional[dict] = None

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        if v is not None:
            # Must contain action if present
            if "action" in v and v["action"] not in ("search", "on_search"):
                raise ValueError(f"Invalid action: {v['action']}")
            # transaction_id must be a string if present
            if "transaction_id" in v and not isinstance(v["transaction_id"], str):
                raise ValueError("transaction_id must be a string")
        return v


class SubscribeRequest(BaseModel):
    """Stub for ONDC registry subscription."""
    subscriber_id: str
    subscriber_url: str
    domain: str = "nic2004:52110"
    city: str = "*"
    country: str = "IND"

    @field_validator("subscriber_id")
    @classmethod
    def validate_subscriber_id(cls, v):
        if not v or len(v) > 256:
            raise ValueError("subscriber_id must be 1-256 characters")
        return v.strip()

    @field_validator("subscriber_url")
    @classmethod
    def validate_subscriber_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("subscriber_url must be a valid URL")
        return v.strip()

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v):
        if not re.match(r"^[a-zA-Z0-9:]+$", v):
            raise ValueError("Invalid domain format")
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v):
        if not re.match(r"^[A-Z]{2,3}$", v):
            raise ValueError("country must be a 2-3 letter ISO code")
        return v.upper()


@router.get("/status")
@limiter.limit("30/minute")
async def ondc_status(request: Request):
    """
    ONDC sandbox connection health check.
    Returns BPP identity and catalog availability.
    """
    try:
        all_sellers = get_all_seller_ids()
        seller_count = len(all_sellers) if all_sellers else 0
    except Exception:
        seller_count = 0

    return {
        "status": "sandbox_ready",
        "bpp_id": BPP_ID,
        "bpp_uri": BPP_URI,
        "protocol_version": "1.1.0",
        "domain": "nic2004:52110",
        "registered_sellers": seller_count,
        "endpoints": {
            "on_search": f"{BPP_URI}/on_search",
            "subscribe": f"{BPP_URI}/subscribe",
            "status": f"{BPP_URI}/status",
        },
    }


@router.post("/on_search")
@limiter.limit("20/minute")
async def on_search(request: Request, body: SearchRequest):
    """
    Respond to an ONDC buyer app /search request with seller catalogs.

    In production, this would validate the BAP signature, check the search
    intent, and respond with matching catalogs. For sandbox, it returns
    all registered seller catalogs.
    """
    transaction_id = None
    if body.context:
        transaction_id = body.context.get("transaction_id")

    try:
        all_sellers = get_all_seller_ids()
    except Exception as e:
        logger.error(f"Failed to fetch sellers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sellers")

    if not all_sellers:
        return {
            "context": {"action": "on_search", "transaction_id": transaction_id},
            "message": {"catalog": {"bpp/providers": []}},
        }

    # For sandbox, return the first seller's catalog
    seller_id = all_sellers[0] if isinstance(all_sellers[0], str) else all_sellers[0].get("seller_id", "")

    try:
        catalog = get_catalog(seller_id)
        profile = get_seller_profile(seller_id)
    except Exception as e:
        logger.error(f"Failed to fetch catalog for {seller_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch catalog")

    ondc_response = build_on_search_response(
        seller_id=seller_id,
        catalog=catalog,
        seller_profile=profile,
        transaction_id=transaction_id,
    )

    items_count = len(ondc_response.get("message", {}).get("catalog", {}).get("bpp/providers", [{}])[0].get("items", []))
    logger.info(f"on_search response: {items_count} items")
    return ondc_response


@router.post("/subscribe")
@limiter.limit("5/minute")
async def subscribe(request: Request, body: SubscribeRequest):
    """
    Stub for ONDC registry subscription.

    In production, this would:
    1. Generate and submit a signing key to the ONDC registry
    2. Complete the on_subscribe challenge
    3. Store the subscription details

    For now, returns a successful acknowledgment.
    """
    logger.info(f"ONDC subscribe request: {body.subscriber_id} ({body.domain})")

    return {
        "status": "ACK",
        "message": "Subscription acknowledged (sandbox mode)",
        "subscriber_id": body.subscriber_id,
        "bpp_id": BPP_ID,
        "note": "In production, this would complete the ONDC on_subscribe challenge and register with the registry.",
    }
