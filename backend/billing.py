"""Pricing plans, usage tracking, and billing helpers."""
import base64
import hmac
import hashlib
import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from db import get_catalog, get_supabase_client, log_activity, ensure_profile_exists
from env_utils import get_env_value

logger = logging.getLogger(__name__)
TRIAL_DAYS = 7


PLANS: dict[str, dict[str, Any]] = {
    "free": {
        "id": "free",
        "name": "Free",
        "price_inr": 0,
        "interval": "month",
        "description": "Basic inventory control for a single seller workspace.",
        "limits": {
            "products": 100,
            "whatsapp_messages": 100,
        },
        "features": [
            "100 products",
            "100 WhatsApp messages/month",
            "Basic dashboard",
        ],
        "media_features": False,
        "api_access": False,
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_inr": 199,
        "interval": "month",
        "description": "For active sellers managing inventory through chat, voice, and images.",
        "limits": {
            "products": None,
            "whatsapp_messages": None,
        },
        "features": [
            "Unlimited products",
            "Unlimited WhatsApp updates",
            "Voice note support",
            "Image recognition",
            "Priority support",
        ],
        "media_features": True,
        "api_access": False,
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "price_inr": 999,
        "interval": "month",
        "description": "For larger operations that need richer workflows and commercial support.",
        "limits": {
            "products": None,
            "whatsapp_messages": None,
        },
        "features": [
            "Unlimited products",
            "Unlimited WhatsApp updates",
            "Voice and image automation",
            "Multi-store support",
            "API access",
            "Custom branding",
            "ONDC listing support",
        ],
        "media_features": True,
        "api_access": True,
    },
}


class BillingError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 403):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass
class UsageSummary:
    current_plan: str
    billing_status: str
    products_used: int
    products_limit: Optional[int]
    messages_used: int
    messages_limit: Optional[int]
    period_start: str


def normalize_plan(plan: str | None) -> str:
    if not plan:
        return "free"
    value = str(plan).strip().lower()
    if value in PLANS:
        return value
    return "free"


def get_plan_definition(plan: str | None) -> dict[str, Any]:
    return PLANS[normalize_plan(plan)]


def _default_billing_profile() -> dict[str, Any]:
    return {
        "billing_plan": "pro",
        "billing_status": "trialing",
        "billing_interval": "trial",
        "billing_provider": "trial",
        "billing_email": "",
        "razorpay_customer_id": "",
        "razorpay_subscription_id": "",
        "plan_started_at": None,
        "current_period_start": None,
        "current_period_end": None,
        "trial_started_at": None,
        "trial_ends_at": None,
    }


def _get_billing_profile(seller_id: str, jwt_token: str | None = None) -> dict[str, Any]:
    ensure_profile_exists(seller_id, jwt_token, service_role=jwt_token is None)
    sb = get_supabase_client(jwt_token, use_service_role=jwt_token is None)
    try:
        response = (
            sb.table("profiles")
            .select(
                "id,billing_plan,billing_status,billing_interval,billing_provider,billing_email,"
                "razorpay_customer_id,razorpay_subscription_id,plan_started_at,current_period_start,current_period_end,"
                "trial_started_at,trial_ends_at"
            )
            .eq("id", seller_id)
            .limit(1)
            .execute()
        )
        if response.data:
            profile = {**_default_billing_profile(), **response.data[0]}
            return _apply_trial_state(seller_id, profile, jwt_token=jwt_token)
    except Exception as e:
        logger.error(f"_get_billing_profile error: {e}")
    return _default_billing_profile()


def _update_profile_billing(
    seller_id: str,
    updates: dict[str, Any],
    jwt_token: str | None = None,
):
    ensure_profile_exists(seller_id, jwt_token, service_role=jwt_token is None)
    sb = get_supabase_client(jwt_token, use_service_role=jwt_token is None)
    payload = {"id": seller_id, **updates}
    try:
        sb.table("profiles").upsert(payload).execute()
    except Exception as e:
        logger.error(f"_update_profile_billing error: {e}")


def _get_latest_subscription(seller_id: str, jwt_token: str | None = None) -> dict[str, Any] | None:
    sb = get_supabase_client(jwt_token, use_service_role=jwt_token is None)
    try:
        response = (
            sb.table("subscriptions")
            .select("*")
            .eq("seller_id", seller_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.error(f"_get_latest_subscription error: {e}")
    return None


def _insert_subscription_event(
    seller_id: str,
    plan: str,
    status: str,
    provider: str,
    amount_inr: int,
    jwt_token: str | None = None,
    provider_order_id: str = "",
    provider_payment_id: str = "",
    provider_subscription_id: str = "",
    metadata: dict[str, Any] | None = None,
    current_period_start: str | None = None,
    current_period_end: str | None = None,
):
    sb = get_supabase_client(jwt_token, use_service_role=jwt_token is None)
    payload = {
        "seller_id": seller_id,
        "plan_id": plan,
        "status": status,
        "provider": provider,
        "amount_inr": amount_inr,
        "currency": "INR",
        "provider_order_id": provider_order_id or None,
        "provider_payment_id": provider_payment_id or None,
        "provider_subscription_id": provider_subscription_id or None,
        "current_period_start": current_period_start,
        "current_period_end": current_period_end,
        "metadata": metadata or {},
    }
    try:
        sb.table("subscriptions").insert(payload).execute()
    except Exception as e:
        logger.error(f"_insert_subscription_event error: {e}")


def _apply_trial_state(
    seller_id: str,
    profile: dict[str, Any],
    jwt_token: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    trial_started_raw = profile.get("trial_started_at")
    trial_ends_raw = profile.get("trial_ends_at")
    billing_plan = normalize_plan(profile.get("billing_plan"))
    billing_status = str(profile.get("billing_status") or "active")
    has_paid_reference = bool(profile.get("razorpay_subscription_id"))

    trial_started = _parse_created_at(trial_started_raw)
    trial_ends = _parse_created_at(trial_ends_raw)

    should_bootstrap_trial = (
        not has_paid_reference
        and billing_status not in {"cancelled"}
        and trial_started is None
    )

    if should_bootstrap_trial:
        trial_started = now
        trial_ends = now + timedelta(days=TRIAL_DAYS)
        updates = {
            "billing_plan": "pro",
            "billing_status": "trialing",
            "billing_interval": "trial",
            "billing_provider": "trial",
            "plan_started_at": trial_started.isoformat(),
            "current_period_start": trial_started.isoformat(),
            "current_period_end": trial_ends.isoformat(),
            "trial_started_at": trial_started.isoformat(),
            "trial_ends_at": trial_ends.isoformat(),
            "updated_at": now.isoformat(),
        }
        _update_profile_billing(seller_id, updates, jwt_token=jwt_token)
        _insert_subscription_event(
            seller_id=seller_id,
            plan="pro",
            status="trialing",
            provider="trial",
            amount_inr=0,
            jwt_token=jwt_token,
            metadata={"source": "auto_trial"},
            current_period_start=trial_started.isoformat(),
            current_period_end=trial_ends.isoformat(),
        )
        return {**profile, **updates}

    if billing_status == "trialing" and trial_ends is not None and trial_ends <= now:
        updates = {
            "billing_plan": "free",
            "billing_status": "active",
            "billing_interval": "month",
            "billing_provider": "trial_expired",
            "current_period_start": now.isoformat(),
            "current_period_end": None,
            "updated_at": now.isoformat(),
        }
        _update_profile_billing(seller_id, updates, jwt_token=jwt_token)
        _insert_subscription_event(
            seller_id=seller_id,
            plan="free",
            status="active",
            provider="trial_expired",
            amount_inr=0,
            jwt_token=jwt_token,
            metadata={"source": "trial_expired"},
            current_period_start=now.isoformat(),
            current_period_end=None,
        )
        return {**profile, **updates}

    if billing_plan == "free" and billing_status == "trialing":
        profile["billing_plan"] = "pro"

    return profile


def get_current_plan(seller_id: str, jwt_token: str | None = None) -> str:
    profile = _get_billing_profile(seller_id, jwt_token=jwt_token)
    return normalize_plan(profile.get("billing_plan"))


def _get_catalog_items_count(seller_id: str, jwt_token: str | None = None) -> int:
    catalog = get_catalog(seller_id, jwt_token=jwt_token, service_role=jwt_token is None)
    try:
        items = catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
        return len(items) if isinstance(items, list) else 0
    except (KeyError, IndexError, TypeError):
        return 0


def _month_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _parse_created_at(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _count_monthly_messages(seller_id: str, jwt_token: str | None = None) -> int:
    sb = get_supabase_client(jwt_token, use_service_role=jwt_token is None)
    try:
        response = (
            sb.table("activity_log")
            .select("action, created_at")
            .eq("seller_id", seller_id)
            .eq("action", "WHATSAPP_RECEIVED")
            .order("id", desc=True)
            .limit(2000)
            .execute()
        )
    except Exception as e:
        logger.error(f"_count_monthly_messages error: {e}")
        return 0

    month_start = _month_start()
    count = 0
    for row in response.data or []:
        created_at = _parse_created_at(row.get("created_at"))
        if created_at is None or created_at >= month_start:
            count += 1
    return count


def get_usage_summary(seller_id: str, jwt_token: str | None = None) -> UsageSummary:
    profile = _get_billing_profile(seller_id, jwt_token=jwt_token)
    plan = normalize_plan(profile.get("billing_plan"))
    plan_def = get_plan_definition(plan)
    period_start_value = profile.get("current_period_start")
    parsed_period_start = _parse_created_at(period_start_value)
    if parsed_period_start is None:
        parsed_period_start = _month_start()
    return UsageSummary(
        current_plan=plan,
        billing_status=str(profile.get("billing_status") or "active"),
        products_used=_get_catalog_items_count(seller_id, jwt_token=jwt_token),
        products_limit=plan_def["limits"]["products"],
        messages_used=_count_monthly_messages(seller_id, jwt_token=jwt_token),
        messages_limit=plan_def["limits"]["whatsapp_messages"],
        period_start=parsed_period_start.date().isoformat(),
    )


def get_billing_summary(seller_id: str, jwt_token: str | None = None) -> dict[str, Any]:
    usage = get_usage_summary(seller_id, jwt_token=jwt_token)
    plan_def = get_plan_definition(usage.current_plan)
    profile = _get_billing_profile(seller_id, jwt_token=jwt_token)
    latest_subscription = _get_latest_subscription(seller_id, jwt_token=jwt_token)

    def _remaining(limit_value: Optional[int], used: int) -> Optional[int]:
        if limit_value is None:
            return None
        return max(limit_value - used, 0)

    return {
        "seller_id": seller_id,
        "current_plan": usage.current_plan,
        "billing_status": usage.billing_status,
        "billing_provider": profile.get("billing_provider") or "",
        "billing_email": profile.get("billing_email") or "",
        "current_period_end": profile.get("current_period_end"),
        "razorpay_customer_id": profile.get("razorpay_customer_id") or "",
        "razorpay_subscription_id": profile.get("razorpay_subscription_id") or "",
        "trial_started_at": profile.get("trial_started_at"),
        "trial_ends_at": profile.get("trial_ends_at"),
        "current_plan_details": plan_def,
        "usage": {
            "period_start": usage.period_start,
            "products": {
                "used": usage.products_used,
                "limit": usage.products_limit,
                "remaining": _remaining(usage.products_limit, usage.products_used),
            },
            "whatsapp_messages": {
                "used": usage.messages_used,
                "limit": usage.messages_limit,
                "remaining": _remaining(usage.messages_limit, usage.messages_used),
            },
        },
        "trial_days_remaining": (
            max((_parse_created_at(profile.get("trial_ends_at")) - datetime.now(timezone.utc)).days + 1, 0)
            if usage.billing_status == "trialing" and _parse_created_at(profile.get("trial_ends_at")) is not None
            else 0
        ),
        "latest_subscription": latest_subscription,
        "plans": list(PLANS.values()),
    }


def assert_product_limit_or_raise(
    seller_id: str,
    proposed_total: int,
    jwt_token: str | None = None,
    source: str = "dashboard",
):
    usage = get_usage_summary(seller_id, jwt_token=jwt_token)
    if usage.products_limit is not None and proposed_total > usage.products_limit:
        message = f"Free plan allows up to {usage.products_limit} products. Upgrade to Pro for unlimited inventory."
        log_activity(
            seller_id,
            "BILLING_LIMIT_BLOCKED",
            details=json.dumps(
                {
                    "type": "products",
                    "plan": usage.current_plan,
                    "used": usage.products_used,
                    "limit": usage.products_limit,
                    "source": source,
                }
            ),
            jwt_token=jwt_token,
            service_role=jwt_token is None,
        )
        raise BillingError("PRODUCT_LIMIT_EXCEEDED", message)


def assert_message_limit_or_raise(
    seller_id: str,
    projected_messages: int | None = None,
    jwt_token: str | None = None,
    source: str = "whatsapp",
):
    usage = get_usage_summary(seller_id, jwt_token=jwt_token)
    next_messages = projected_messages if projected_messages is not None else usage.messages_used + 1
    if usage.messages_limit is not None and next_messages > usage.messages_limit:
        message = (
            f"Free plan includes {usage.messages_limit} WhatsApp messages per month. "
            "Upgrade to Pro for unlimited chat-based inventory updates."
        )
        log_activity(
            seller_id,
            "BILLING_LIMIT_BLOCKED",
            details=json.dumps(
                {
                    "type": "whatsapp_messages",
                    "plan": usage.current_plan,
                    "used": usage.messages_used,
                    "limit": usage.messages_limit,
                    "source": source,
                }
            ),
            jwt_token=jwt_token,
            service_role=jwt_token is None,
        )
        raise BillingError("MESSAGE_LIMIT_EXCEEDED", message)


def assert_media_feature_or_raise(
    seller_id: str,
    media_type: str,
    jwt_token: str | None = None,
):
    usage = get_usage_summary(seller_id, jwt_token=jwt_token)
    plan_def = get_plan_definition(usage.current_plan)
    if plan_def["media_features"]:
        return

    feature_label = "voice notes" if media_type == "audio" else "image recognition"
    message = f"{feature_label.capitalize()} is available on the Pro plan and above."
    log_activity(
        seller_id,
        "BILLING_FEATURE_BLOCKED",
        details=json.dumps(
            {
                "type": media_type,
                "plan": usage.current_plan,
            }
        ),
        jwt_token=jwt_token,
        service_role=jwt_token is None,
    )
    raise BillingError("FEATURE_NOT_IN_PLAN", message)


def record_plan_change(
    seller_id: str,
    plan: str,
    source: str = "dashboard",
    jwt_token: str | None = None,
    payment_reference: str = "",
    provider: str = "manual",
    provider_order_id: str = "",
    provider_payment_id: str = "",
    provider_subscription_id: str = "",
    billing_email: str = "",
):
    normalized = normalize_plan(plan)
    plan_def = get_plan_definition(normalized)
    now = datetime.now(timezone.utc)
    current_period_start = now.isoformat()
    current_period_end = (now + timedelta(days=30)).isoformat()
    status = "active"

    _update_profile_billing(
        seller_id,
        {
            "billing_plan": normalized,
            "billing_status": status,
            "billing_interval": plan_def["interval"],
            "billing_provider": provider,
            "billing_email": billing_email or None,
            "razorpay_subscription_id": provider_subscription_id or None,
            "plan_started_at": now.isoformat(),
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
            "updated_at": now.isoformat(),
        },
        jwt_token=jwt_token,
    )

    _insert_subscription_event(
        seller_id=seller_id,
        plan=normalized,
        status=status,
        provider=provider,
        amount_inr=plan_def["price_inr"],
        jwt_token=jwt_token,
        provider_order_id=provider_order_id,
        provider_payment_id=provider_payment_id or payment_reference,
        provider_subscription_id=provider_subscription_id,
        metadata={"source": source},
        current_period_start=current_period_start,
        current_period_end=current_period_end,
    )

    log_activity(
        seller_id,
        "PLAN_CHANGED",
        details=json.dumps(
            {
                "plan": normalized,
                "source": source,
                "provider": provider,
                "provider_order_id": provider_order_id,
                "payment_reference": payment_reference,
                "changed_at": datetime.now(timezone.utc).isoformat(),
            }
        ),
        jwt_token=jwt_token,
        service_role=jwt_token is None,
    )


def create_razorpay_order(seller_id: str, plan: str) -> dict[str, Any]:
    plan_def = get_plan_definition(plan)
    if plan_def["price_inr"] <= 0:
        return {"status": "free", "plan": "free"}

    key_id = get_env_value("RAZORPAY_KEY_ID")
    key_secret = get_env_value("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise BillingError(
            "PAYMENT_NOT_CONFIGURED",
            "Razorpay is not configured yet. We recorded your upgrade request.",
            status_code=503,
        )

    payload = {
        "amount": int(plan_def["price_inr"] * 100),
        "currency": "INR",
        "receipt": f"{seller_id}-{plan}-{int(time.time())}",
        "notes": {"seller_id": seller_id, "plan": plan},
    }
    auth = base64.b64encode(f"{key_id}:{key_secret}".encode("utf-8")).decode("utf-8")
    request = urllib.request.Request(
        "https://api.razorpay.com/v1/orders",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        logger.error(f"Razorpay order creation failed: {body}")
        raise BillingError("PAYMENT_PROVIDER_ERROR", "Failed to create Razorpay order.", status_code=502)
    except Exception as e:
        logger.error(f"Razorpay order creation error: {e}")
        raise BillingError("PAYMENT_PROVIDER_ERROR", "Failed to create Razorpay order.", status_code=502)

    return {
        "provider": "razorpay",
        "key_id": key_id,
        "order_id": data.get("id", ""),
        "amount": payload["amount"],
        "currency": payload["currency"],
        "plan": plan,
        "name": "ONDC Super Seller",
        "description": f"{plan_def['name']} plan subscription",
    }


def record_checkout_created(
    seller_id: str,
    plan: str,
    order_id: str,
    jwt_token: str | None = None,
):
    plan_def = get_plan_definition(plan)
    _insert_subscription_event(
        seller_id=seller_id,
        plan=plan,
        status="pending",
        provider="razorpay",
        amount_inr=plan_def["price_inr"],
        jwt_token=jwt_token,
        provider_order_id=order_id,
        metadata={"state": "checkout_created"},
    )


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    key_secret = get_env_value("RAZORPAY_KEY_SECRET")
    if not key_secret:
        return False
    body = f"{order_id}|{payment_id}".encode("utf-8")
    digest = hmac.new(key_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, signature)
