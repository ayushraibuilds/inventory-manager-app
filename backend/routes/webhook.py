"""WhatsApp webhook router — receives messages, processes via AI agent, sends replies."""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks

from routes.auth import get_jwt_token, verify_twilio_signature, send_whatsapp_reply
from routes.seller_ratelimit import is_rate_limited
from agent import process_whatsapp_message
from billing import BillingError, assert_media_feature_or_raise, assert_message_limit_or_raise, assert_product_limit_or_raise
from lang_detect import detect as detect_language
from reply_templates import format_reply
from price_reference import get_price_suggestion
from db import (
    get_seller_id_by_phone,
    get_seller_profile,
    get_conversation_history,
    get_catalog,
    save_catalog,
    log_activity,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhook"])


@router.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    token = None
    """
    Webhook to receive incoming WhatsApp messages.
    Schedules the message through the AI agent and instantly returns a 200 OK reply to Twilio.
    """
    try:
        form_data = await request.form()
        form_dict = dict(form_data)
        seller_id = form_dict.get("From", "unknown_seller")
        raw_message = form_dict.get("Body", "")
        message_id = form_dict.get("MessageSid", "")
        logger.info(
            f"WEBHOOK TRACER: Incoming form payload: From={seller_id} Length={len(raw_message)} MessageSid={message_id}"
        )

        if message_id:
            from redis_client import redis_client
            try:
                # Atomically set and check if this is the first time we see this message from Twilio
                acquired = await redis_client.set(f"webhook_dedup:{message_id}", "1", ex=86400, nx=True)
                if not acquired:
                    logger.info(f"WEBHOOK TRACER: Deduplicating retried message: {message_id}")
                    return {"status": "deduplicated"}
            except Exception as e:
                logger.warning(f"Redis deduplication error (likely offline), skipping deduplication: {e}")

        if not verify_twilio_signature(request, form_dict):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"WEBHOOK TRACER: Form parsing or signature validation crashed with {e}!"
        )
        try:
            json_data = await request.json()
            seller_id = json_data.get("from_number", "unknown_seller")
            raw_message = json_data.get("message", "")
        except Exception:
            seller_id = "unknown_seller"
            raw_message = ""

    # --- Detect language early (for onboarding & error messages) ---
    lang_result = detect_language(raw_message)
    detected_lang = lang_result.lang_code
    logger.info(f"Language detected: {detected_lang} (method={lang_result.method})")

    # --- Phone to UUID Resolution ---
    extracted_phone = seller_id.replace("whatsapp:", "")

    real_seller_id = await asyncio.to_thread(get_seller_id_by_phone, extracted_phone)
    if not real_seller_id:
        logger.warning(f"Unknown phone number: {extracted_phone}")
        reply = format_reply(detected_lang, "UNREGISTERED")
        await asyncio.to_thread(send_whatsapp_reply, seller_id, reply)  # type: ignore
        return {"status": "error", "message": "Unregistered Seller Phone"}

    seller_id = real_seller_id

    try:
        await asyncio.to_thread(assert_message_limit_or_raise, seller_id, None, None, "whatsapp")
    except BillingError as e:
        await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", e.message)
        return {"status": "plan_limit", "message": e.message}

    # --- Voice Note / Image Interception ---
    image_media_url = None
    try:
        num_media = int(form_dict.get("NumMedia", 0))
        if num_media > 0:
            content_type = form_dict.get("MediaContentType0", "")
            if content_type.startswith("audio/"):
                await asyncio.to_thread(assert_media_feature_or_raise, seller_id, "audio", None)
                media_url = form_dict.get("MediaUrl0")
                if media_url:
                    from voice_processor import voice_processor

                    transcription = await voice_processor.transcribe_audio(media_url)
                    logger.info(f"🎤 Voice Note Transcribed: {transcription}")
                    if transcription:
                        raw_message = transcription
                        # Re-detect language on transcribed text
                        lang_result = detect_language(raw_message)
                        detected_lang = lang_result.lang_code
            elif content_type.startswith("image/"):
                await asyncio.to_thread(assert_media_feature_or_raise, seller_id, "image", None)
                image_media_url = form_dict.get("MediaUrl0")
                logger.info(f"📷 Image received: {content_type}")
    except BillingError as e:
        await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", e.message)
        return {"status": "plan_feature_blocked", "message": e.message}
    except Exception as e:
        logger.error(f"Media Processing Error: {e}")
        reply = format_reply(detected_lang, "VOICE_ERROR")
        await asyncio.to_thread(
            send_whatsapp_reply, f"whatsapp:{extracted_phone}", reply,
        )  # type: ignore
        return {"status": "error", "message": "Media Processing Error"}

    # --- Per-Seller Rate Limit ---
    is_limited = await asyncio.to_thread(is_rate_limited, seller_id)
    if is_limited:
        logger.warning(f"RATE LIMITED seller: {seller_id}")
        reply = format_reply(detected_lang, "RATE_LIMITED")
        await asyncio.to_thread(
            send_whatsapp_reply, f"whatsapp:{extracted_phone}", reply,
        )
        return {"status": "rate_limited"}

    # --- Seller Onboarding ---
    profile = await asyncio.to_thread(get_seller_profile, seller_id, None)
    if not profile.get("store_name"):
        welcome = format_reply(detected_lang, "ONBOARDING")
        await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", welcome)  # type: ignore
        await asyncio.to_thread(
        log_activity,
        seller_id,
        "SELLER_ONBOARDED",
        "New seller interacted",
        "",
        token,
        True,
    )

    # --- Audit Trail: Log incoming message ---
    await asyncio.to_thread(
        log_activity,
        seller_id,
        "WHATSAPP_RECEIVED",
        "",
        raw_message[:500],
        token,
        True,
    )

    # --- Fetch conversation memory ---
    conversation_history = await asyncio.to_thread(get_conversation_history, seller_id, 3, None)

    ack = format_reply(detected_lang, "RECEIVED")
    await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", ack)  # type: ignore

    print("WEBHOOK TRACER: Queuing Agent processing thread")
    from celery_app import process_webhook_task
    from redis_client import redis_client
    
    celery_queued = False
    try:
        # Check if Redis is actually alive before blocking on Celery
        await asyncio.wait_for(redis_client.ping(), timeout=1.0)
        process_webhook_task.delay(
            raw_message, seller_id, extracted_phone, detected_lang, conversation_history, image_media_url, token
        )
        logger.info("Successfully queued webhook processing via Celery.")
        celery_queued = True
    except Exception as e:
        logger.warning(f"Redis ping or Celery fail, bypassing Celery and using FastAPI BackgroundTasks: {type(e).__name__} {e}")

    if not celery_queued:
        background_tasks.add_task(
            process_webhook_background, raw_message, seller_id, extracted_phone, detected_lang, conversation_history, image_media_url, token
        )

    return {"status": "received"}


async def process_webhook_background(
    raw_message: str, seller_id: str, extracted_phone: str,
    detected_lang: str = "en", conversation_history: list = None,
    image_media_url: str = None, token: str = None,
):
    # --- Image cataloging path ---
    if image_media_url:
        try:
            from image_processor import process_product_image
            items = await asyncio.to_thread(process_product_image, image_media_url, detected_lang)
            if items:
                # Build catalog entries and merge into seller's catalog
                import uuid
                existing_catalog = get_catalog(seller_id, service_role=True)
                try:
                    existing_items = existing_catalog["bpp/catalog"]["bpp/providers"][0].get("items", [])
                except (KeyError, IndexError):
                    existing_items = []

                for item_data in items:
                    beckn_item = {
                        "id": str(uuid.uuid4()),
                        "category_id": item_data.get("category_id", "Grocery"),
                        "descriptor": {"name": item_data["name"], "short_desc": f"{item_data['quantity']} {item_data['unit']} of {item_data['name']}"},
                        "price": {"currency": "INR", "value": str(item_data["price_inr"])},
                        "quantity": {"available": {"count": item_data["quantity"]}},
                        "unit": item_data["unit"],
                    }
                    existing_items.append(beckn_item)

                await asyncio.to_thread(
                    assert_product_limit_or_raise,
                    seller_id,
                    len(existing_items),
                    None,
                    "image_catalog",
                )

                updated_catalog = {
                    "bpp/catalog": {"bpp/providers": [{"id": f"provider_{seller_id}", "descriptor": {"name": f"Super Seller: {seller_id}"}, "items": existing_items}]}
                }
                saved = save_catalog(seller_id, updated_catalog, service_role=True)
                if not saved:
                    raise RuntimeError("CATALOG_SAVE_ERROR")

                names = [f"{i['name']} (₹{i['price_inr']})" for i in items]
                reply = f"📷 Extracted {len(items)} items from your photo:\n" + "\n".join(f"• {n}" for n in names)
                reply += f"\n\nYour catalog now has {len(existing_items)} items."
                log_activity(seller_id, "IMAGE_CATALOG", details=f"{len(items)} items from image", service_role=True)
                sent = send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)
                log_action = "WHATSAPP_SENT" if sent else "WHATSAPP_SEND_FAILED"
                log_activity(seller_id, log_action, details=reply[:500], jwt_token=token, service_role=True)
                return
        except Exception as e:
            logger.error(f"Image Processing Error: {e}")
            reply = format_reply(detected_lang, "ERROR")
            send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)
            return

    # --- Standard text/voice processing path ---
    try:
        result = await asyncio.to_thread(
            process_whatsapp_message, raw_message, seller_id, conversation_history or []
        )  # type: ignore
    except BillingError as e:
        logger.warning(f"Billing guard blocked WhatsApp action: {e.code} {e.message}")
        reply = e.message
        send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)
        return
    except Exception as e:
        logger.error(f"Agent Processing Error: {e}")
        reply = format_reply(detected_lang, "ERROR")
        send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)
        return

    # Read language from agent result (may be more accurate than early detection)
    lang = result.get("detected_language", detected_lang)
    intent = result.get("intent", "UNKNOWN")
    reply = ""

    if intent == "ADD":
        catalog = result.get("ondc_beckn_json", {})
        try:
            items = (
                catalog.get("bpp/catalog", {})
                .get("bpp/providers", [{}])[0]
                .get("items", [])
            )
            item_count = len(items)
            entities = result.get("extracted_product_entities")
            if entities and hasattr(entities, "items") and len(entities.items) > 0:
                names = [
                    f"{e.name} (₹{e.price_inr} × {e.quantity_value} {e.unit})"
                    for e in entities.items
                ]
                reply = format_reply(lang, "ADD", items=", ".join(names), count=item_count)

                # --- Price intelligence hints ---
                price_hints = []
                for e in entities.items:
                    try:
                        suggestion = get_price_suggestion(e.name, float(e.price_inr), e.unit)
                        if suggestion and suggestion.status != "competitive":
                            price_hints.append(suggestion.suggestion)
                    except (ValueError, TypeError):
                        pass
                if price_hints:
                    reply += "\n" + "\n".join(price_hints)
            else:
                reply = format_reply(lang, "ADD_SIMPLE", count=item_count)
        except Exception:
            reply = format_reply(lang, "ADD_SIMPLE", count="?")
        log_activity(seller_id, "ADD_VIA_WHATSAPP", raw_message, service_role=True)
    elif intent == "UPDATE":
        reply = format_reply(lang, "UPDATE")
        log_activity(seller_id, "UPDATE_VIA_WHATSAPP", raw_message, service_role=True)
    elif intent == "DELETE":
        reply = format_reply(lang, "DELETE")
        log_activity(seller_id, "DELETE_VIA_WHATSAPP", raw_message, service_role=True)
    elif intent == "FAQ":
        faq_answer = result.get("faq_answer", "")
        reply = format_reply(lang, "FAQ", answer=faq_answer) if faq_answer else format_reply(lang, "UNKNOWN")
        log_activity(seller_id, "FAQ_VIA_WHATSAPP", raw_message, service_role=True)
    else:
        reply = format_reply(lang, "UNKNOWN")
        log_activity(seller_id, "UNKNOWN_INTENT", raw_message, service_role=True)

    # Send reply
    sent = send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)

    # --- Audit Trail: Log outgoing reply ---
    log_activity(
        seller_id,
        "WHATSAPP_SENT" if sent else "WHATSAPP_SEND_FAILED",
        item_name="",
        details=reply[:500],
        jwt_token=token,
        service_role=True,
    )
