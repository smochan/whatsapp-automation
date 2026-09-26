# Architecture

## Goal

A standalone, multi-tenant WhatsApp automation platform for travel businesses. The first release focuses on inbound customer service, lead/CRM extraction, booking workflows, human handoff, and follow-up handling. Marketing/broadcast tooling is intentionally out of MVP.

## Runtime

```text
Customer
  -> WhatsApp
  -> Meta Cloud API webhook
  -> FastAPI ingestion
  -> PostgreSQL/Supabase
  -> Redis/ARQ worker
  -> Laya router
  -> business tools / knowledge retrieval
  -> low-cost LLM when generation is required
  -> WhatsApp Cloud API
```

The webhook endpoint should remain fast and idempotent. It persists the event/message and returns 200; AI work runs in the background worker.

## Local processes

API:

```bash
uvicorn app.main:app --reload
```

Worker:

```bash
arq app.workers.message_worker.WorkerSettings
```

Both processes use the same backend image in deployment; the worker is a separate service/process.

## Tenancy

Every business-facing entity carries `organization_id`. A WhatsApp phone number maps to exactly one organization. Tenant isolation will be enforced both in application services and Supabase RLS once dashboard authentication is introduced.

## WhatsApp service window

Every inbound customer message refreshes `window_expires_at` to 24 hours after the customer message timestamp. The system must check this field before sending business-initiated follow-ups. When the window is closed, only an approved WhatsApp template should be used for a follow-up.

## AI boundary

Laya is an orchestration/router dependency, not the source of truth. It decides intent and routing. Tools retrieve authoritative package, booking, customer and knowledge data. The LLM receives only the minimum relevant context needed to generate a response. If no authoritative context is found, the current orchestrator refuses to generate a business-fact answer rather than hallucinating.

## Future TripSynk integration

TripSynk will be an optional external integration behind an API boundary. The standalone product must remain useful without TripSynk.
