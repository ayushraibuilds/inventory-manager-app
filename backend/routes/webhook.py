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
    create_pending_approval,
    get_latest_pending_approval,
    resolve_pending_approval,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhook"])

APPROVAL_CONFIRM_WORDS = {"confirm", "approved", "approve", "yes", "haan", "ha", "ok", "okay"}
APPROVAL_CANCEL_WORDS = {"cancel", "no", "nahi", "nahin", "reject", "ignore", "stop"}


def _normalize_whatsapp_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _get_approval_decision(text: str) -> Optional[str]:
    normalized = _normalize_whatsapp_text(text)
    if normalized in APPROVAL_CONFIRM_WORDS:
        return "confirmed"
    if normalized in APPROVAL_CANCEL_WORDS:
        return "cancelled"
    return None


def _format_item_bullets(items: list[dict]) -> str:
    if not items:
        return "• No items extracted"

    bullets = []
    for item in items[:5]:
        name = str(item.get("name", "Unknown")).strip() or "Unknown"
        price = str(item.get("price_inr", "0") or "0")
        quantity = item.get("quantity", 1)
        unit = str(item.get("unit", "piece") or "piece")
        bullets.append(f"• {name} (₹{price} x {quantity} {unit})")
    return "\n".join(bullets)


def _assess_image_confidence(items: list[dict]) -> tuple[bool, str]:
    if not items:
        return True, "I could not confidently extract any products from the image."

    weak_signals = 0
    for item in items:
        name = str(item.get("name", "") or "").strip().lower()
        if not name or name == "unknown":
            weak_signals += 2
        try:
            price = float(item.get("price_inr", 0) or 0)
        except (TypeError, ValueError):
            price = 0
        if price <= 0:
            weak_signals += 1
        try:
            quantity = int(item.get("quantity", 1) or 1)
        except (TypeError, ValueError):
            quantity = 0
        if quantity <= 0:
            weak_signals += 1

    if weak_signals >= max(2, len(items)):
        return True, "Some extracted items are missing price or product details."
    return False, ""


def _assess_voice_confidence(transcript: str) -> tuple[bool, str]:
    normalized = _normalize_whatsapp_text(transcript)
    words = normalized.split()
    uncertain_words = {"umm", "uh", "hmm", "maybe", "shayad", "kuch", "something"}
    uncertain_count = sum(1 for word in words if word in uncertain_words)
    if len(words) < 4:
        return True, "The voice note transcript looks too short to apply automatically."
    if uncertain_count >= 2:
        return True, "The voice note transcript looks ambiguous."
    return False, ""


def _build_approval_summary(pending: dict) -> str:
    source_type = pending.get("source_type", "update")
    reason = pending.get("reason", "")
    items = pending.get("items") or []
    transcript = pending.get("transcript", "")

    if source_type == "voice":
        summary = f"Transcript:\n“{transcript or 'No transcript available'}”"
    else:
        summary = "Extracted items:\n" + _format_item_bullets(items)

    if reason:
        summary += f"\n\nReason: {reason}"
    return summary


def _merge_image_items_into_catalog(seller_id: str, items: list[dict]) -> tuple[bool, int]:
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
            "descriptor": {
                "name": item_data["name"],
                "short_desc": f"{item_data['quantity']} {item_data['unit']} of {item_data['name']}",
            },
            "price": {"currency": "INR", "value": str(item_data["price_inr"])},
            "quantity": {"available": {"count": item_data["quantity"]}},
            "unit": item_data["unit"],
        }
        existing_items.append(beckn_item)

    assert_product_limit_or_raise(
        seller_id,
        len(existing_items),
        None,
        "image_catalog",
    )

    updated_catalog = {
        "bpp/catalog": {
            "bpp/providers": [
                {
                    "id": f"provider_{seller_id}",
                    "descriptor": {"name": f"Super Seller: {seller_id}"},
                    "items": existing_items,
                }
            ]
        }
    }
    return save_catalog(seller_id, updated_catalog, service_role=True), len(existing_items)


def _deliver_agent_reply(
    result: dict,
    seller_id: str,
    extracted_phone: str,
    raw_message: str,
    detected_lang: str = "en",
    token: str = None,
):
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

    sent = send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)
    log_activity(
        seller_id,
        "WHATSAPP_SENT" if sent else "WHATSAPP_SEND_FAILED",
        item_name="",
        details=reply[:500],
        jwt_token=token,
        service_role=True,
    )


async def process_pending_approval_background(
    pending: dict,
    seller_id: str,
    extracted_phone: str,
    detected_lang: str = "en",
    token: str = None,
):
    approval_id = pending.get("approval_id", "")
    source_type = pending.get("source_type", "")
    if not approval_id:
        send_whatsapp_reply(
            f"whatsapp:{extracted_phone}",
            format_reply(detected_lang, "NO_PENDING_APPROVAL"),
        )
        return

    try:
        if source_type == "voice":
            transcript = pending.get("transcript", "")
            history = get_conversation_history(seller_id, 3, None)
            result = await asyncio.to_thread(
                process_whatsapp_message,
                transcript,
                seller_id,
                history,
            )
            resolve_pending_approval(
                seller_id,
                approval_id,
                "confirmed",
                details={"source_type": source_type},
                service_role=True,
            )
            confirmed = format_reply(
                detected_lang,
                "APPROVAL_CONFIRMED",
                summary="Applying your approved voice note now.",
            )
            send_whatsapp_reply(f"whatsapp:{extracted_phone}", confirmed)
            _deliver_agent_reply(
                result,
                seller_id,
                extracted_phone,
                transcript,
                detected_lang,
                token,
            )
            return

        items = pending.get("items") or []
        saved, total_count = await asyncio.to_thread(_merge_image_items_into_catalog, seller_id, items)
        if not saved:
            raise RuntimeError("CATALOG_SAVE_ERROR")

        resolve_pending_approval(
            seller_id,
            approval_id,
            "confirmed",
            details={"source_type": source_type, "item_count": len(items)},
            service_role=True,
        )
        log_activity(
            seller_id,
            "IMAGE_CATALOG",
            details=f"{len(items)} items confirmed from image",
            service_role=True,
        )
        reply = format_reply(
            detected_lang,
            "APPROVAL_CONFIRMED",
            summary=(
                f"Added {len(items)} extracted items.\n"
                f"{_format_item_bullets(items)}\n\nYour catalog now has {total_count} items."
            ),
        )
        sent = send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)
        log_activity(
            seller_id,
            "WHATSAPP_SENT" if sent else "WHATSAPP_SEND_FAILED",
            details=reply[:500],
            jwt_token=token,
            service_role=True,
        )
    except BillingError as e:
        send_whatsapp_reply(f"whatsapp:{extracted_phone}", e.message)
    except Exception as e:
        logger.error(f"Pending approval processing error: {e}")
        send_whatsapp_reply(f"whatsapp:{extracted_phone}", format_reply(detected_lang, "ERROR"))


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
    was_voice_note = False
    try:
        num_media = int(form_dict.get("NumMedia", 0))
        if num_media > 0:
            content_type = form_dict.get("MediaContentType0", "")
            if content_type.startswith("audio/"):
                was_voice_note = True
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

    approval_decision = _get_approval_decision(raw_message)
    if approval_decision:
        pending = await asyncio.to_thread(get_latest_pending_approval, seller_id, None, True)
        if not pending:
            reply = format_reply(detected_lang, "NO_PENDING_APPROVAL")
            await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", reply)
            return {"status": "no_pending_approval"}
        if approval_decision == "cancelled":
            await asyncio.to_thread(
                resolve_pending_approval,
                seller_id,
                pending["approval_id"],
                "cancelled",
                {"source_type": pending.get("source_type", "")},
                None,
                True,
            )
            reply = format_reply(detected_lang, "APPROVAL_CANCELLED")
            await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", reply)
            return {"status": "approval_cancelled"}

        ack = format_reply(detected_lang, "RECEIVED")
        await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", ack)
        background_tasks.add_task(
            process_pending_approval_background,
            pending,
            seller_id,
            extracted_phone,
            detected_lang,
            token,
        )
        return {"status": "approval_processing"}

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
            low_confidence, reason = _assess_image_confidence(items)
            if low_confidence:
                pending = await asyncio.to_thread(
                    create_pending_approval,
                    seller_id,
                    "image",
                    {
                        "items": items,
                        "reason": reason,
                        "raw_message": raw_message[:500],
                    },
                    None,
                    True,
                )
                reply = format_reply(
                    detected_lang,
                    "APPROVAL_REQUIRED",
                    summary=_build_approval_summary(pending),
                )
                sent = send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)
                log_activity(
                    seller_id,
                    "WHATSAPP_SENT" if sent else "WHATSAPP_SEND_FAILED",
                    details=reply[:500],
                    jwt_token=token,
                    service_role=True,
                )
                return

            saved, total_count = await asyncio.to_thread(_merge_image_items_into_catalog, seller_id, items)
            if not saved:
                raise RuntimeError("CATALOG_SAVE_ERROR")

            names = [f"{i['name']} (₹{i['price_inr']})" for i in items]
            reply = f"📷 Extracted {len(items)} items from your photo:\n" + "\n".join(f"• {n}" for n in names)
            reply += f"\n\nYour catalog now has {total_count} items."
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
    low_confidence_voice, voice_reason = _assess_voice_confidence(raw_message)
    if was_voice_note and voice_reason and low_confidence_voice:
        pending = await asyncio.to_thread(
            create_pending_approval,
            seller_id,
            "voice",
            {
                "transcript": raw_message[:500],
                "reason": voice_reason,
            },
            None,
            True,
        )
        reply = format_reply(
            detected_lang,
            "APPROVAL_REQUIRED",
            summary=_build_approval_summary(pending),
        )
        sent = send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)
        log_activity(
            seller_id,
            "WHATSAPP_SENT" if sent else "WHATSAPP_SEND_FAILED",
            details=reply[:500],
            jwt_token=token,
            service_role=True,
        )
        return

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
    _deliver_agent_reply(result, seller_id, extracted_phone, raw_message, detected_lang, token)
