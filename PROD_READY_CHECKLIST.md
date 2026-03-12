# Production Readiness Checklist

## Done

- Seller-scoped dashboard and API routes require auth instead of falling back to broad service-role access.
- Production startup fails fast when critical backend vars are missing or insecure.
- Twilio signature validation is enabled in production and supports proxied deployments through `PUBLIC_URL`.
- Basic `/health` checks verify Supabase connectivity without forcing third-party API calls.
- Security headers middleware is enabled.
- Webhook processing has retry protection, Redis-backed deduplication, and immediate seller acknowledgements.
- LLM calls have retry logic, timeout protection, and a circuit breaker.
- Docker production compose file exists for backend, dashboard, Redis, and Celery.
- Railway deployment path has been validated with `NODE_ENV=production`, `PUBLIC_URL`, and a working backend start command.
- Deployment config-as-code now exists for the current hosting setup:
  - `backend/railway.json` for shared Railway build and restart policy
  - `dashboard/vercel.json` for the Next.js dashboard deploy
- `.env.production.example` now documents the exact backend and dashboard production variables.
- Landing-page messaging now reflects the real product: seller inventory management through WhatsApp.
- Public legal pages now exist for Privacy Policy and Terms of Service.

## Still Required Before Calling It Fully Prod Ready

### Critical

- Rotate all previously exposed secrets and confirm old values are revoked.
- Make Twilio webhook delivery observable in production with HTTP log review or request alerting.
- Decide whether ONDC is sandbox-only or a true launch surface. If true, replace the stubbed subscription/search flow with real signature validation and registry integration.

### Important

- Finish frontend accessibility cleanup:
  - remove remaining lint warnings
  - add missing image alt handling where applicable
  - confirm keyboard-only navigation on key dashboard flows
- Update README deployment steps so they match the current Railway setup and current landing-page positioning.
- Add error tracking/observability such as Sentry and alerting for failed Twilio, Groq, or Supabase operations.
- Keep Railway service start commands documented and in sync with the codebase:
  - backend API
  - Celery worker
  - Celery beat

### Nice To Have

- Add screenshots or short GIFs to README and landing/supporting docs.
- Add daily seller-facing stock summary and low-confidence AI confirmation flows.
