"""WhatsApp webhook router — receives messages, processes via AI agent, sends replies."""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks

from routes.auth import get_jwt_token, verify_twilio_signature, send_whatsapp_reply
from routes.seller_ratelimit import is_rate_limited
from agent import process_whatsapp_message
from db import (
    get_seller_id_by_phone,
    get_seller_profile,
    log_activity,
)

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
        print(
            f"WEBHOOK TRACER: Incoming form payload: From={seller_id} Length={len(raw_message)}"
        )

        if not verify_twilio_signature(request, form_dict):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    except HTTPException:
        raise
    except Exception as e:
        print(
            f"WEBHOOK TRACER: Form parsing or signature validation crashed with {e}!"
        )
        try:
            json_data = await request.json()
            seller_id = json_data.get("from_number", "unknown_seller")
            raw_message = json_data.get("message", "")
        except Exception:
            seller_id = "unknown_seller"
            raw_message = ""

    # --- Voice Note Interception ---
    try:
        num_media = int(form_dict.get("NumMedia", 0))
        if num_media > 0:
            content_type = form_dict.get("MediaContentType0", "")
            if content_type.startswith("audio/"):
                media_url = form_dict.get("MediaUrl0")
                if media_url:
                    from voice_processor import voice_processor

                    transcription = await voice_processor.transcribe_audio(media_url)
                    print(f"🎤 Voice Note Transcribed: {transcription}")
                    if transcription:
                        raw_message = transcription
    except Exception as e:
        print(f"Voice Note Error: {e}")
        await asyncio.to_thread(
            send_whatsapp_reply,
            seller_id,
            "⚠️ We couldn't transcribe your voice note at the moment. Please send a text message instead.",
        )  # type: ignore
        return {"status": "error", "message": "Voice Transcription Error"}

    # --- Phone to UUID Resolution ---
    extracted_phone = seller_id.replace("whatsapp:", "")

    real_seller_id = get_seller_id_by_phone(extracted_phone)
    if not real_seller_id:
        print(f"Unknown phone number: {extracted_phone}")
        reply = "⚠️ Welcome! To create an ONDC catalog, please sign up through our Super Seller Dashboard and link your phone number first."
        await asyncio.to_thread(send_whatsapp_reply, seller_id, reply)  # type: ignore
        return {"status": "error", "message": "Unregistered Seller Phone"}

    seller_id = real_seller_id

    # --- Per-Seller Rate Limit ---
    if is_rate_limited(seller_id):
        print(f"RATE LIMITED seller: {seller_id}")
        await asyncio.to_thread(
            send_whatsapp_reply,
            f"whatsapp:{extracted_phone}",
            "⏳ You're sending messages too quickly! Please wait a moment before sending another update.",
        )
        return {"status": "rate_limited"}

    # --- Seller Onboarding ---
    profile = get_seller_profile(seller_id)
    if not profile.get("store_name"):
        welcome = (
            "🎉 *Welcome to ONDC Super Seller!*\n\n"
            "I'm your AI catalog assistant. Just tell me what you sell in Hindi or English:\n\n"
            '• "10 kg atta for 450 rupees"\n'
            '• "5 packet Maggi at 60 each"\n\n'
            "I'll create your ONDC catalog automatically! 📱\n\n"
            "_Tip: Visit the dashboard to set your store name and address._"
        )
        await asyncio.to_thread(send_whatsapp_reply, f"whatsapp:{extracted_phone}", welcome)  # type: ignore
        log_activity(
            seller_id,
            "SELLER_ONBOARDED",
            details="New seller interacted",
            jwt_token=token,
        )

    # --- Audit Trail: Log incoming message ---
    log_activity(
        seller_id,
        "WHATSAPP_RECEIVED",
        item_name="",
        details=raw_message[:500],
        jwt_token=token,
    )

    print("WEBHOOK TRACER: Queuing Agent processing thread")
    background_tasks.add_task(
        process_webhook_background, raw_message, seller_id, extracted_phone, token
    )

    return {"status": "received"}


async def process_webhook_background(
    raw_message: str, seller_id: str, extracted_phone: str, token: str = None
):
    try:
        result = await asyncio.to_thread(process_whatsapp_message, raw_message, seller_id)  # type: ignore
    except Exception as e:
        print(f"Agent Processing Error: {e}")
        reply = "⚠️ Sorry, our AI is currently experiencing high traffic or a timeout. Please try again in a moment."
        send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)
        return

    # Build and send WhatsApp reply
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
                reply = f"✅ Added: {', '.join(names)}.\nYour catalog now has {item_count} items."
            else:
                reply = f"✅ Catalog updated. You now have {item_count} items."
        except Exception:
            reply = "✅ Catalog updated successfully."
        log_activity(seller_id, "ADD_VIA_WHATSAPP", raw_message)
    elif intent == "UPDATE":
        reply = "✅ Item updated successfully."
        log_activity(seller_id, "UPDATE_VIA_WHATSAPP", raw_message)
    elif intent == "DELETE":
        reply = "🗑️ Item removed from your catalog."
        log_activity(seller_id, "DELETE_VIA_WHATSAPP", raw_message)
    else:
        reply = '🤔 Sorry, I couldn\'t understand that. Try something like:\n• "Add 10 kg atta at 450 rupees"\n• "Remove Maggi from my catalog"\n• "Update rice price to 60 rupees"'
        log_activity(seller_id, "UNKNOWN_INTENT", raw_message)

    # Send reply
    send_whatsapp_reply(f"whatsapp:{extracted_phone}", reply)

    # --- Audit Trail: Log outgoing reply ---
    log_activity(
        seller_id,
        "WHATSAPP_SENT",
        item_name="",
        details=reply[:500],
        jwt_token=token,
    )
