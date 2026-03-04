# Contributing to ONDC Super Seller

Thank you for contributing! Here's how to get started.

## Development Setup

### Prerequisites
- Python 3.12+, Node.js 20+ (or Docker)
- Supabase project (free tier)
- Groq API key (free tier)

### Quick Start

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/ondc-super-seller.git
cd ondc-super-seller

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in credentials

# Frontend  
cd ../dashboard
npm install
```

Or with Docker: `docker compose up`

## Development Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Run tests: `cd backend && pytest tests/ -v`
4. Check types: `cd dashboard && npx tsc --noEmit`
5. Open a PR against `main`

CI will automatically run backend tests and frontend build on every PR.

## Project Structure

| Directory | Purpose |
|---|---|
| `backend/routes/` | API route handlers (one per domain) |
| `backend/tests/` | pytest test files |
| `backend/db.py` | Supabase database operations |
| `backend/langgraph_agent.py` | AI agent (intent + entity extraction) |
| `dashboard/src/app/` | Next.js pages (file-based routing) |
| `dashboard/src/components/` | Reusable React components |
| `dashboard/src/lib/` | Shared utilities (i18n, etc.) |

## Code Style

- **Python**: Standard formatting, type hints preferred
- **TypeScript**: Strict mode, no `any` unless necessary
- **Commits**: Descriptive messages, present tense ("Add price check endpoint")

## Adding a New API Endpoint

1. Create or edit a route file in `backend/routes/`
2. Register it in `backend/server.py`
3. Add tests in `backend/tests/`
4. Update the API table in `README.md`

## Adding a New Dashboard Page

1. Create a new directory in `dashboard/src/app/`
2. Add `page.tsx` (the page) and `layout.tsx` (metadata)
3. Add navigation link in `dashboard/src/app/dashboard/page.tsx`
4. Add translations to `dashboard/src/lib/i18n.ts`

## Running Tests

```bash
# Backend (130 tests)
cd backend && source venv/bin/activate
pytest tests/ -v

# Frontend type check
cd dashboard
npx tsc --noEmit
```
