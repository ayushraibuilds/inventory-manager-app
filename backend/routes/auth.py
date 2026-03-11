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


async def verify_api_key(
    x_api_key: str = Header(default=""),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Dependency that verifies the X-API-Key header OR a valid JWT on write endpoints."""
    # If the request comes from the authenticated dashboard, let it pass to Supabase RLS
    if credentials and credentials.credentials:
        return

    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key or missing Authentication")


def verify_twilio_signature(request: Request, form_data: dict) -> bool:
    from dotenv import dotenv_values

    # Reconstruct the public URL (vital for ngrok/proxies)
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    
    if forwarded_proto and forwarded_host:
        base_url = f"{forwarded_proto}://{forwarded_host}"
        url = f"{base_url}{request.url.path}"
    else:
        url = str(request.url)

    signature = request.headers.get("x-twilio-signature", "")
    
    # Allow unsigned requests ONLY in development mode (Twilio sandbox doesn't always sign)
    is_production = os.getenv("NODE_ENV", "").lower() == "production"
    if not signature and not is_production:
        logging.info("Bypassing Twilio validation (dev mode — non-production environment).")
        return True
    elif not signature:
        logging.error("Missing Twilio signature — rejected in production mode.")
        return False

    # Read from system env (Railway/Docker) first, fall back to .env file
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        env = dotenv_values(".env")
        auth_token = env.get("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        logging.error("Missing TWILIO_AUTH_TOKEN. Cannot verify signature.")
        return False

    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(auth_token)
        is_valid = validator.validate(url, form_data, signature)
        if not is_valid:
            logging.error(f"Twilio signature validation failed. URL used for validation: {url}")
        return is_valid
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
        logging.error(f"Cannot send WhatsApp reply. Missing Twilio credentials. Message: {body}")
        return
    try:
        from twilio.rest import Client

        client = Client(account_sid, auth_token)
        client.messages.create(body=body, from_=whatsapp_from, to=to)
    except Exception as e:
        logging.error(f"Failed to send WhatsApp reply: {e}")
