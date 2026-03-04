"""
Image-based catalog extraction using Groq Vision.

Processes product images sent via WhatsApp, extracts items using
llama-3.2-90b-vision-preview, and returns structured CatalogExtraction.
"""
import base64
import logging
import os
import uuid

import requests
from requests.auth import HTTPBasicAuth
from dotenv import dotenv_values
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Vision model on Groq (free tier)
VISION_MODEL = "llama-3.2-90b-vision-preview"


def _download_twilio_image(media_url: str) -> bytes:
    """Download an image from Twilio's media URL with authentication."""
    env = dotenv_values(".env")
    twilio_sid = env.get("TWILIO_ACCOUNT_SID", "")
    twilio_auth = env.get("TWILIO_AUTH_TOKEN", "")

    if not twilio_sid or not twilio_auth:
        raise ValueError("Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in .env")

    response = requests.get(
        media_url,
        auth=HTTPBasicAuth(twilio_sid, twilio_auth),
        timeout=30,
    )
    if response.status_code != 200:
        raise Exception(f"Failed to download image: HTTP {response.status_code}")

    return response.content


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda rs: logger.warning(f"Vision attempt {rs.attempt_number} failed, retrying..."),
)
def _call_vision_api(image_b64: str, lang_code: str = "en") -> dict:
    """Send an image to Groq Vision and get structured product extraction."""
    env = dotenv_values(".env")
    groq_key = env.get("GROQ_API_KEY", "")
    if not groq_key:
        raise ValueError("Missing GROQ_API_KEY in .env")

    client = Groq(api_key=groq_key)

    lang_context = ""
    if lang_code == "hi":
        lang_context = "The shopkeeper speaks Hindi/Hinglish. Product labels may be in Hindi."

    prompt = f"""You are an AI assistant for an Indian shopkeeper inventory system.
Analyze this image and extract ALL visible products/items.

For each product, provide:
- name: The product name (clean, standardized)
- price_inr: The price in INR if visible (number only, no symbols). Use 0 if not visible.
- quantity: The count of items visible. Default to 1 if unclear.
- unit: The unit (kg, liter, piece, packet, etc.)
- category: One of: Grocery, F&B, Health & Wellness, Beauty & Personal Care, Home & Decor, Electronics, Other

{lang_context}

IMPORTANT: Return your response as a JSON object with this exact structure:
{{"items": [{{"name": "Product Name", "price_inr": "100", "quantity": 5, "unit": "kg", "category": "Grocery"}}]}}

Extract EVERY product you can identify. Do not skip any items."""

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}",
                        },
                    },
                ],
            }
        ],
        temperature=0.1,
        max_tokens=2048,
    )

    text = response.choices[0].message.content or ""
    logger.info(f"Vision API raw response length: {len(text)}")
    return _parse_vision_response(text)


def _parse_vision_response(text: str) -> dict:
    """Parse the vision model's text response into structured items."""
    import json
    import re

    # Try to extract JSON from the response
    # The model may wrap it in ```json ... ``` or return it directly
    json_match = re.search(r'\{[\s\S]*"items"[\s\S]*\}', text)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if "items" in data and isinstance(data["items"], list):
                return data
        except json.JSONDecodeError:
            pass

    # Fallback: try to parse the entire text as JSON
    try:
        data = json.loads(text)
        if "items" in data:
            return data
    except json.JSONDecodeError:
        pass

    logger.warning(f"Could not parse vision response as JSON: {text[:200]}")
    return {"items": []}


def process_product_image(media_url: str, lang_code: str = "en") -> list:
    """
    Full pipeline: download image → encode → call Vision API → return items.

    Returns a list of dicts: [{"name": ..., "price_inr": ..., "quantity": ..., "unit": ..., "category": ...}]
    """
    try:
        # 1. Download
        image_bytes = _download_twilio_image(media_url)
        logger.info(f"Downloaded image: {len(image_bytes)} bytes")

        # 2. Encode to base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # 3. Call Vision API
        result = _call_vision_api(image_b64, lang_code)

        # 4. Normalize items
        items = []
        for raw in result.get("items", []):
            items.append({
                "name": str(raw.get("name", "Unknown")).strip(),
                "price_inr": str(raw.get("price_inr", "0")),
                "quantity": int(raw.get("quantity", 1)),
                "unit": str(raw.get("unit", "piece")),
                "category_id": str(raw.get("category", "Grocery")),
            })

        logger.info(f"Extracted {len(items)} items from image")
        return items

    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise
