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
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from asgi_correlation_id import CorrelationIdMiddleware, correlation_id
from pythonjsonlogger import jsonlogger

load_dotenv()

# Rate limiter (shared across all routers)
limiter = Limiter(key_func=get_remote_address)


# Filter out the Next.js polling spam from the uvicorn access logger
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /api/catalog") == -1

class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id.get() or "no-id"
        return True

def setup_logging():
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(correlation_id)s %(name)s %(message)s'
    )
    log_handler.setFormatter(formatter)
    log_handler.addFilter(CorrelationIdFilter())
    
    logging.basicConfig(handlers=[log_handler], level=logging.INFO, force=True)
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

setup_logging()


# --- App setup ---
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Modern lifespan handler replacing deprecated @app.on_event."""
    yield


app = FastAPI(title="ONDC Super Seller API", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
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
from routes.ondc import router as ondc_router
from routes.images import router as images_router

# Backward-compatible /api/* paths
app.include_router(webhook_router)
app.include_router(catalog_router)
app.include_router(orders_router)
app.include_router(sellers_router)
app.include_router(images_router)

# Versioned /api/v1/* paths (same handlers, new prefix)
app.include_router(catalog_v1_router)
app.include_router(orders_v1_router)
app.include_router(sellers_v1_router)

# ONDC sandbox endpoints
app.include_router(ondc_router)
