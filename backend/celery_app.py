import os
import asyncio
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from reply_templates import format_reply

load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ondc_super_seller",
    broker=redis_url,
    backend=redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Optional: define beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "check-low-stock-every-hour": {
        "task": "celery_app.check_low_stock_alerts_task",
        "schedule": 3600.0,
    },
    "send-daily-stock-summary": {
        "task": "celery_app.send_daily_stock_summary_task",
        "schedule": crontab(hour=9, minute=0),
    },
}

def run_async_block(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@celery_app.task
def check_low_stock_alerts_task():
    from db import get_all_seller_ids, get_seller_profile, get_catalog, log_activity
    from routes.auth import send_whatsapp_reply

    seller_ids = get_all_seller_ids()
    for sid in seller_ids:
        profile = get_seller_profile(sid)
        if not profile.get("low_stock_alerts"):
            continue

        catalog = get_catalog(sid, service_role=True)
        try:
            items = (
                catalog.get("bpp/catalog", {})
                .get("bpp/providers", [{}])[0]
                .get("items", [])
            )
        except (KeyError, IndexError):
            continue

        low_stock_items = []
        for item in items:
            try:
                qty = int(
                    str(
                        item.get("quantity", {})
                        .get("available", {})
                        .get("count", 0)
                        or 0
                    )
                )
                name = item.get("descriptor", {}).get("name", "Unknown")
                if qty < 5:
                    low_stock_items.append(f"  • {name} ({qty} left)")
            except (ValueError, TypeError):
                continue

        if low_stock_items:
            alert = (
                f"⚠️ *Low Stock Alert*\n\n"
                f"The following items are running low:\n"
                + "\n".join(low_stock_items)
                + "\n\n_Update stock via WhatsApp or dashboard._"
            )
            phone = profile.get("phone", "")
            if phone:
                send_whatsapp_reply(phone, alert)
            log_activity(
                sid,
                "LOW_STOCK_ALERT",
                details=f"{len(low_stock_items)} items low",
                service_role=True,
            )


def _build_daily_stock_summary(items: list[dict], lang_code: str = "en") -> str:
    total_products = len(items)
    total_value = 0.0
    low_stock = []

    for item in items:
        name = item.get("descriptor", {}).get("name", "Unknown")
        try:
            qty = int(
                str(item.get("quantity", {}).get("available", {}).get("count", 0) or 0)
            )
        except (TypeError, ValueError):
            qty = 0
        try:
            price = float(item.get("price", {}).get("value", 0) or 0)
        except (TypeError, ValueError):
            price = 0.0
        total_value += qty * price
        if qty < 5:
            low_stock.append(f"• {name} ({qty} left)")

    summary_lines = [
        f"Total products: {total_products}",
        f"Estimated stock value: ₹{int(total_value)}",
        f"Low stock items: {len(low_stock)}",
    ]
    if low_stock:
        summary_lines.append("Top low stock items:")
        summary_lines.extend(low_stock[:3])

    return format_reply(lang_code, "DAILY_SUMMARY", summary="\n".join(summary_lines))


@celery_app.task
def send_daily_stock_summary_task():
    from db import get_all_seller_ids, get_seller_profile, get_catalog, log_activity
    from routes.auth import send_whatsapp_reply

    seller_ids = get_all_seller_ids()
    for sid in seller_ids:
        profile = get_seller_profile(sid)
        phone = profile.get("phone", "")
        if not phone:
            continue

        catalog = get_catalog(sid, service_role=True)
        try:
            items = (
                catalog.get("bpp/catalog", {})
                .get("bpp/providers", [{}])[0]
                .get("items", [])
            )
        except (KeyError, IndexError):
            items = []

        lang_code = (profile.get("preferred_language") or "en").split("-")[0]
        summary = _build_daily_stock_summary(items, lang_code)
        send_whatsapp_reply(phone, summary)
        log_activity(
            sid,
            "DAILY_STOCK_SUMMARY_SENT",
            details=f"summary_sent products={len(items)}",
            service_role=True,
        )

@celery_app.task
def process_webhook_task(
    raw_message: str,
    seller_id: str,
    extracted_phone: str,
    detected_lang: str,
    conversation_history: list,
    image_media_url: str,
    token: str = None,
):
    from routes.webhook import process_webhook_background
    run_async_block(
        process_webhook_background(
            raw_message,
            seller_id,
            extracted_phone,
            detected_lang,
            conversation_history,
            image_media_url,
            token,
        )
    )
