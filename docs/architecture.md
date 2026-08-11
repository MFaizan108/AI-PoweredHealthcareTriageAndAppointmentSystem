# Architecture

## Request flow (production)

```
                    Internet
                       │
                       ▼
                    Nginx            (planned — Phase 9; local dev serves Django directly)
                       │
                       ▼
                 Django / Gunicorn   (REST API, JWT auth, RBAC, throttling, audit middleware)
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   PostgreSQL        Redis          Celery Worker
   (isolated          (cache +           │
    container)         Celery broker)    ▼
                                      Celery Beat  (hourly appointment-reminder schedule)
```

In local dev, Postgres/Redis run in isolated Docker containers (unique project name and ports —
deliberately separated from any other Docker projects on the same machine), while Django itself runs via
`manage.py runserver`. `docker-compose.yml` also defines `web`/`celery_worker`/`celery_beat` services for a
fully containerized run.

## Django apps

| App | Responsibility |
|---|---|
| `accounts` | Custom `User` model (role-based), JWT login, 2FA, email verification, password reset |
| `departments` | Hospital departments |
| `patients` | Patient profile, auto-created from `User` via signal |
| `doctors` | Doctor profile, availability windows, leave |
| `appointments` | Booking, slot/token generation, queue, waitlist, feedback |
| `medical_records` | EMR entries and diagnoses |
| `prescriptions` | Prescriptions + line items, PDF export |
| `laboratory` | Lab test requests and reports |
| `notifications` | In-app notifications, created internally by other apps |
| `triage` | Rule-based triage engine, AI provider settings, triage assessments, emergency guidance |
| `ai_assistant` | RAG-based patient assistant (retriever + LLM), hospital FAQ content |
| `billing` | Invoices and payments |
| `messaging` | Patient–doctor messaging, scoped to a shared appointment |
| `analytics` | Read-only aggregation endpoints for admin dashboards |
| `audit_logs` | Middleware-driven audit trail |

## AI architecture (triage)

Three layers, only the first of which is currently implemented as anything beyond a pass-through:

1. **Layer 1 — Rule engine** (`triage/rules_engine.py`): keyword-matches free-text symptoms against a
   seeded `Symptom` catalog, sums severity weights, and applies threshold/red-flag logic to produce an
   urgency level (`emergency` / `high` / `moderate` / `low`) and a suggested department. This is the
   authoritative layer — it runs even if the LLM is unavailable.
2. **Layer 2 — ML classifier**: **not implemented.** No validated clinical dataset exists to train one
   responsibly; see [Limitations](../README.md#limitations) once the top-level README is written (Phase 14).
3. **Layer 3 — LLM summary** (`triage/llm.py`): takes the Layer 1 output and produces a short, plain-language
   explanation for the patient. Dual-provider — **Ollama** (local) or **Groq** (cloud), selected at runtime
   via the admin-editable `AIProviderSettings` singleton. Every triage result carries a fixed disclaimer
   (`TriageAssessment.DISCLAIMER`) — the LLM output is explanatory only and never overrides the Layer 1
   urgency/department decision.

The AI assistant (`ai_assistant`) reuses the same `ask_llm()` provider abstraction for a separate RAG
Q&A feature — see [permissions.md](permissions.md#ai-assistant-authorization-is-never-bypassed-by-the-llm)
for how it stays permission-scoped.

## Security-relevant middleware/settings

- `audit_logs.middleware.AuditLogMiddleware` — last in `MIDDLEWARE`, logs mutating requests and login
  attempts after the view has run (so it captures the authenticated user DRF resolved).
- `rest_framework_simplejwt.token_blacklist` — backs refresh-token rotation/blacklisting.
- Field-level encryption (`triage/crypto.py`, Fernet, key derived from `DJANGO_SECRET_KEY`) — used for the
  Groq API key at rest.
- Production-only hardening block in `settings.py` (`if not DEBUG:`) — HSTS, secure cookies, SSL redirect,
  referrer policy, content-type sniffing protection.

## API documentation stack

- **OpenAPI schema**: `drf-spectacular`, served at `/api/schema/`.
- **Swagger UI**: `/api/docs/` — interactive, supports "Authorize" with a bearer token for trying real
  requests.
- **ReDoc**: `/api/redoc/` — read-only, better for a static reference view.
- Per-app `views.py` files carry `@extend_schema`/`@extend_schema_view` decorators only where DRF can't
  auto-derive a request/response shape (plain `APIView`s with no `serializer_class`) — standard
  `ModelViewSet`s are documented automatically from their `serializer_class`.

## API versioning strategy

The API is **unversioned in the URL today** (`/api/<app>/...`) — acceptable for a project with no external
consumers yet. The agreed strategy for when a breaking change is needed:

- Introduce `/api/v2/<app>/...` alongside the existing `/api/<app>/...` (implicitly "v1"), rather than
  mutating v1 in place.
- Keep v1 running unchanged until consumers migrate; do not silently change response shapes on existing
  endpoints.
- Prefer **additive, backwards-compatible changes** (new optional fields, new endpoints) over version bumps
  wherever possible — most of this project's evolution so far (billing, messaging, analytics, waitlist,
  feedback...) has been additive for exactly this reason.
