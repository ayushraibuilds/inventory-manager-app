"""Billing routes for pricing plans, usage summary, and checkout intents."""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from billing import (
    BillingError,
    create_razorpay_order,
    get_billing_summary,
    normalize_plan,
    record_checkout_created,
    record_plan_change,
    verify_razorpay_signature,
)
from db import log_activity
from routes.auth import get_jwt_token, require_authenticated_request

router = APIRouter(tags=["billing"])
v1_router = APIRouter(prefix="/api/v1", tags=["billing v1"])


class BillingCheckoutRequest(BaseModel):
    seller_id: str
    plan: str


class BillingConfirmRequest(BaseModel):
    seller_id: str
    plan: str
    razorpay_order_id: str = ""
    razorpay_payment_id: str = ""
    razorpay_signature: str = ""


@router.get("/api/billing/summary", dependencies=[Depends(require_authenticated_request)])
async def billing_summary(seller_id: str, token: str | None = Depends(get_jwt_token)):
    return get_billing_summary(seller_id, jwt_token=token)


@router.post("/api/billing/checkout", dependencies=[Depends(require_authenticated_request)])
async def billing_checkout(data: BillingCheckoutRequest, token: str | None = Depends(get_jwt_token)):
    plan = normalize_plan(data.plan)
    if plan == "free":
        record_plan_change(data.seller_id, "free", jwt_token=token, source="dashboard")
        return {"status": "active", "plan": "free"}

    try:
        order = create_razorpay_order(data.seller_id, plan)
    except BillingError as e:
        if e.code == "PAYMENT_NOT_CONFIGURED":
            log_activity(
                data.seller_id,
                "PLAN_UPGRADE_REQUESTED",
                details=json.dumps({"plan": plan, "source": "dashboard"}),
                jwt_token=token,
            )
            return {
                "status": "manual_contact_required",
                "plan": plan,
                "message": e.message,
            }
        raise HTTPException(status_code=e.status_code, detail=e.message)

    log_activity(
        data.seller_id,
        "BILLING_CHECKOUT_CREATED",
        details=json.dumps({"plan": plan, "order_id": order["order_id"]}),
        jwt_token=token,
    )
    record_checkout_created(data.seller_id, plan, order["order_id"], jwt_token=token)
    return {"status": "checkout_required", **order}


@router.post("/api/billing/confirm", dependencies=[Depends(require_authenticated_request)])
async def billing_confirm(data: BillingConfirmRequest, token: str | None = Depends(get_jwt_token)):
    plan = normalize_plan(data.plan)
    if plan != "free":
        if not data.razorpay_order_id or not data.razorpay_payment_id or not data.razorpay_signature:
            raise HTTPException(status_code=400, detail="Missing Razorpay payment confirmation fields")
        if not verify_razorpay_signature(
            data.razorpay_order_id,
            data.razorpay_payment_id,
            data.razorpay_signature,
        ):
            raise HTTPException(status_code=400, detail="Invalid Razorpay signature")

    payment_reference = data.razorpay_payment_id or data.razorpay_order_id
    record_plan_change(
        data.seller_id,
        plan,
        source="razorpay",
        jwt_token=token,
        payment_reference=payment_reference,
        provider="razorpay",
        provider_order_id=data.razorpay_order_id,
        provider_payment_id=data.razorpay_payment_id,
    )
    return {
        "status": "active",
        "plan": plan,
        "summary": get_billing_summary(data.seller_id, jwt_token=token),
    }


v1_router.get("/billing/summary", dependencies=[Depends(require_authenticated_request)])(billing_summary)
v1_router.post("/billing/checkout", dependencies=[Depends(require_authenticated_request)])(billing_checkout)
v1_router.post("/billing/confirm", dependencies=[Depends(require_authenticated_request)])(billing_confirm)
