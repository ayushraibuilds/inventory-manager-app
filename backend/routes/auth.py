"""Auth helpers and dependencies shared across all routers."""
import os
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

API_KEY = os.getenv("API_KEY", "")
security = HTTPBearer(auto_error=False)


async def get_jwt_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    if credentials:
        return credentials.credentials
    return None


async def verify_api_key(x_api_key: str = Header(default="")):
    """Dependency that verifies the X-API-Key header on write endpoints."""
    if not API_KEY:
        return  # No key configured = dev mode, skip auth
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


def verify_twilio_signature(request: Request, form_data: dict) -> bool:
    from dotenv import dotenv_values

    env = dotenv_values(".env")
    auth_token = env.get("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        return True  # Dev mode — skip validation
    try:
        from twilio.request_validator import RequestValidator

        validator = RequestValidator(auth_token)
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        return validator.validate(url, form_data, signature)
    except ImportError:
        logging.warning("twilio package not installed, skipping webhook validation")
        return True


def send_whatsapp_reply(to: str, body: str):
    """Send a WhatsApp reply via Twilio. Silently fails if not configured."""
    from dotenv import dotenv_values

    env = dotenv_values(".env")
    account_sid = env.get("TWILIO_ACCOUNT_SID", "")
    auth_token = env.get("TWILIO_AUTH_TOKEN", "")
    whatsapp_from = env.get("TWILIO_WHATSAPP_FROM", "")

    if not account_sid or not auth_token or not whatsapp_from:
        logging.info(f"[DEV MODE] WhatsApp reply to {to}: {body}")
        return
    try:
        from twilio.rest import Client

        client = Client(account_sid, auth_token)
        client.messages.create(body=body, from_=whatsapp_from, to=to)
    except Exception as e:
        logging.error(f"Failed to send WhatsApp reply: {e}")
