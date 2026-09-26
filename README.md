# WhatsApp Automation

Standalone, multi-tenant WhatsApp automation platform for travel businesses.

## MVP scope

- WhatsApp Cloud API webhook ingestion and signature verification
- 24-hour customer-service window tracking
- Customer, conversation, message and lead data model
- Tenant-scoped knowledge base
- Package search tool
- Laya orchestration adapter
- Low-cost OpenAI-compatible LLM adapter
- Durable Redis/ARQ message processing
- AI response path with human-handoff guardrails
- Booking/payment and organizer dashboard layers to follow
- Marketing/broadcast tooling intentionally excluded from MVP

## Repository layout

- `backend/` — FastAPI API and worker code
- `supabase/migrations/` — database schema
- `docs/` — architecture and implementation notes

## Local backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload
```

The backend requires a PostgreSQL-compatible `DATABASE_URL`. Redis is required for durable AI processing; without `REDIS_URL`, webhook messages are persisted but not queued.

## Security notes

Never commit `.env` or provider tokens. WhatsApp access tokens stored for organizations must be encrypted with `TOKEN_ENCRYPTION_KEY` before production use.
