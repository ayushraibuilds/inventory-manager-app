"""Auth helpers and dependencies shared across all routers."""
import os
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from env_utils import get_env_value

API_KEY = os.getenv("API_KEY", "")
security = HTTPBearer(auto_error=False)


async def get_jwt_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: str = Header(default=""),
) -> Optional[str]:
    if credentials:
        return credentials.credentials
    if API_KEY and x_api_key == API_KEY:
        return "service-role-api-key"
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


async def require_authenticated_request(
    x_api_key: str = Header(default=""),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Reject requests that do not present either a bearer token or the server API key."""
    if credentials and credentials.credentials:
        return

    if API_KEY and x_api_key == API_KEY:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


def verify_twilio_signature(request: Request, form_data: dict) -> bool:
    public_base_url = get_env_value("PUBLIC_URL") or get_env_value("APP_BASE_URL")

    # Reconstruct the public URL (vital for ngrok/proxies)
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    query_string = request.url.query

    if public_base_url:
        url = f"{public_base_url.rstrip('/')}{request.url.path}"
    elif forwarded_proto and forwarded_host:
        base_url = f"{forwarded_proto}://{forwarded_host}"
        url = f"{base_url}{request.url.path}"
    else:
        url = str(request.url)
    if query_string and "?" not in url:
        url = f"{url}?{query_string}"

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
    auth_token = get_env_value("TWILIO_AUTH_TOKEN")
    if not auth_token:
        logging.error("Missing TWILIO_AUTH_TOKEN. Cannot verify signature.")
        return False

    try:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(auth_token)
        is_valid = validator.validate(url, form_data, signature)
        if not is_valid:
            logging.error(
                "Twilio signature validation failed. "
                f"URL={url} host={request.headers.get('host', '')} "
                f"x-forwarded-host={request.headers.get('x-forwarded-host', '')} "
                f"x-forwarded-proto={request.headers.get('x-forwarded-proto', '')}"
            )
        return is_valid
    except ImportError:
        logging.error("twilio package not installed; refusing webhook validation")
        return False if is_production else True


def send_whatsapp_reply(to: str, body: str):
    """Send a WhatsApp reply via Twilio and report whether it succeeded."""
    account_sid = get_env_value("TWILIO_ACCOUNT_SID")
    auth_token = get_env_value("TWILIO_AUTH_TOKEN")
    whatsapp_from = get_env_value("TWILIO_WHATSAPP_FROM")

    if not account_sid or not auth_token or not whatsapp_from:
        logging.error(f"Cannot send WhatsApp reply. Missing Twilio credentials. Message: {body}")
        return False

    if to and not to.startswith("whatsapp:"):
        to = f"whatsapp:{to}"
    try:
        from twilio.rest import Client

        client = Client(account_sid, auth_token)
        client.messages.create(body=body, from_=whatsapp_from, to=to)
        return True
    except Exception as e:
        logging.error(f"Failed to send WhatsApp reply: {e}")
        return False
