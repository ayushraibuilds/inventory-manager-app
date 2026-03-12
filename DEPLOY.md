# ──────────────────────────────────────────────
# ONDC Super Seller — Production Deployment Guide
# ──────────────────────────────────────────────
# Deploy using ONE of the options below.
# All options require the same environment variables.

# ═══════════════════════════════════════════════
# OPTION A: Docker Compose (Self-hosted / VPS)
# ═══════════════════════════════════════════════
#
# 1. Copy and configure .env:
#    cp backend/.env.example backend/.env
#    # Edit backend/.env with real credentials
#
# 2. Start in production mode:
#    docker compose -f docker-compose.prod.yml up -d
#
# 3. Check health:
#    curl http://your-server:8000/health

# ═══════════════════════════════════════════════
# OPTION B: Railway
# ═══════════════════════════════════════════════
#
# 1. Create new Railway project from this repo
# 2. Add a Redis service (built-in addon)
# 3. Create 3 backend-side services from the same repo, all with root directory backend/:
#    a. Backend API
#       Start: uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
#    b. Celery Worker
#       Start: celery -A celery_app worker --loglevel=info --concurrency=2
#    c. Celery Beat
#       Start: celery -A celery_app beat --loglevel=info
# 4. Railway config-as-code lives in backend/railway.json
#    Note: start commands stay in the Railway UI because the API, worker, and beat
#    services all share the same backend/ root.
# 5. Set env vars in Railway dashboard:
#    NODE_ENV=production
#    SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
#    GROQ_API_KEY, JWT_SECRET
#    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
#    PUBLIC_URL=https://your-backend.up.railway.app
#    REDIS_URL=${{Redis.REDIS_URL}}
#    CORS_ORIGINS=https://your-dashboard.vercel.app
# 6. In Public Networking, map the backend service to port 8000
# 7. Point Twilio "When a message comes in" to:
#    https://your-backend.up.railway.app/whatsapp-webhook

# ═══════════════════════════════════════════════
# OPTION C: Render
# ═══════════════════════════════════════════════
#
# 1. Create Web Service from repo (backend/)
#    Build: pip install -r requirements.txt
#    Start: uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
# 2. Add Redis addon
# 3. Create Static Site from repo (dashboard/)
# 4. Set env vars per OPTION B above

# ═══════════════════════════════════════════════
# OPTION D: Vercel (Dashboard only) + Railway/Render (Backend)
# ═══════════════════════════════════════════════
#
# Best option: deploy dashboard on Vercel (free, optimized for Next.js)
# and backend on Railway or Render.
#
# Vercel:
#   1. Import dashboard/ folder
#   2. Vercel config-as-code lives in dashboard/vercel.json
#   3. Set NEXT_PUBLIC_API_URL to your backend URL
#   4. Deploy
#
# Production env reference:
#   See .env.production.example at the repo root for the exact variable set used
#   across Railway backend services and the Vercel dashboard.
