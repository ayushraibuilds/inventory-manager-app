"""
ONDC Super Seller API — Main application entrypoint.

This is a slim orchestrator that:
- Creates the FastAPI app
- Configures CORS, rate limiting, and lifespan
- Includes all modular routers from routes/
"""
import asyncio
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

# Rate limiter (shared across all routers)
limiter = Limiter(key_func=get_remote_address)


# Filter out the Next.js polling spam from the uvicorn access logger
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /api/catalog") == -1


logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


# --- Low Stock Alert Background Task ---
async def check_low_stock_alerts():
    """Background task that runs hourly, checks each seller's inventory,
    and sends WhatsApp alerts if low_stock_alerts is enabled."""
    from db import get_all_seller_ids, get_seller_profile, get_catalog, log_activity
    from routes.auth import send_whatsapp_reply

    token = None
    while True:
        await asyncio.sleep(3600)  # every hour
        try:
            seller_ids = get_all_seller_ids()
            for sid in seller_ids:
                profile = get_seller_profile(sid)
                if not profile.get("low_stock_alerts"):
                    continue

                catalog = get_catalog(sid, jwt_token=token)
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
                        jwt_token=token,
                    )
        except Exception:
            pass  # Never let the background task crash


# --- App setup ---
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Modern lifespan handler replacing deprecated @app.on_event."""
    task = asyncio.create_task(check_low_stock_alerts())
    yield
    task.cancel()


app = FastAPI(title="ONDC Super Seller API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS (environment-based) ---
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3005,http://127.0.0.1:3000,http://192.168.1.34:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include routers ---
from routes.webhook import router as webhook_router
from routes.catalog import router as catalog_router, v1_router as catalog_v1_router
from routes.orders import router as orders_router, v1_router as orders_v1_router
from routes.sellers import router as sellers_router, v1_router as sellers_v1_router

# Backward-compatible /api/* paths
app.include_router(webhook_router)
app.include_router(catalog_router)
app.include_router(orders_router)
app.include_router(sellers_router)

# Versioned /api/v1/* paths (same handlers, new prefix)
app.include_router(catalog_v1_router)
app.include_router(orders_v1_router)
app.include_router(sellers_v1_router)
