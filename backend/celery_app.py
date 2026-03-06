import os
import asyncio
from celery import Celery
from dotenv import load_dotenv

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

        catalog = get_catalog(sid)
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
            send_whatsapp_reply(sid, alert)
            log_activity(
                sid,
                "LOW_STOCK_ALERT",
                details=f"{len(low_stock_items)} items low",
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
