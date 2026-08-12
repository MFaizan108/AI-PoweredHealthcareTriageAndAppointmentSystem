# AI-Powered Healthcare Triage & Appointment System

A hospital operations platform — patient-facing triage, appointment booking, and role-based
dashboards for every part of a clinic's workflow — with a rule-based AI triage engine at its
core and an LLM used only to make that engine's decisions easier to read, never to make them.

Django REST API backend, a React SPA frontend, and a three-layer AI architecture that keeps a
deterministic rule engine authoritative over anything an LLM says. Built phase-by-phase, with
every phase's report and the bugs found along the way kept in [docs/](docs/).

## Overview

A patient describes their symptoms in plain text. A deterministic rule engine — not an LLM —
matches those symptoms against a seeded clinical catalog, scores their severity, and decides an
urgency level (`emergency` / `high` / `moderate` / `low`) and a suggested department. An LLM
then rewrites that already-decided result into a short, readable explanation; it never sets the
urgency or picks the department itself. From there, the patient books an appointment with a
real doctor's real availability, and the system carries that visit through medical records,
prescriptions, lab tests, billing, and messaging — with a receptionist, doctor, lab-staff, and
admin dashboard each seeing exactly the slice of it their role is authorized to see.

Every AI output carries a fixed disclaimer: **this is a preliminary triage / decision-support
tool, not a medical diagnosis.**

## Features

- **AI triage** — rule-based urgency scoring (red-flag symptoms escalate straight to
  `emergency`), department suggestion, and an optional LLM-generated plain-language summary that
  never overrides the rule engine's decision.
- **Appointments** — slot generation from doctor availability, double-booking prevention, queue
  and token numbers, waitlist, cancellation/rescheduling, leave handling.
- **Role dashboards** — Patient, Doctor, Receptionist, Lab Staff, Admin, each with only the
  sections and data their role can see.
- **Electronic medical records** — visit notes and diagnoses tied to an appointment.
- **Prescriptions** — multi-item prescriptions with dosage/frequency/duration, PDF export.
- **Lab workflow** — request → sample collected → processing → report upload, visible to the
  ordering doctor and the patient once complete.
- **Billing** — invoices (consultation + lab charges), partial/full payments.
- **Messaging** — patient–doctor threads scoped to a shared appointment.
- **Notifications** — in-app, generated internally by the apps above (booking, lab report ready,
  new prescription, ...).
- **AI patient assistant (RAG)** — answers a patient's questions using only *their own*
  appointments/prescriptions/lab tests plus hospital FAQs; structurally cannot retrieve another
  patient's data regardless of how the question is phrased (see [AI Architecture](#ai-architecture)).
- **Security** — JWT auth with rotation/blacklisting, 2FA (TOTP + recovery codes), RBAC and
  object-level permissions, rate limiting, full audit logging, CORS/CSP/HSTS, encrypted secrets
  at rest.
- **Observability** — `/health/*` liveness endpoints, Prometheus metrics, an optional
  Grafana/cAdvisor/Flower monitoring stack.
- **AI evaluation** — a dedicated `evaluate_ai` command scores the rule engine against a named
  test matrix, measures live LLM latency/failure/timeout rates per provider, and re-verifies the
  RAG assistant's authorization boundary on every run.

## Architecture

```
                    Internet
                       │
                       ▼
                    Nginx            (HTTPS termination, serves the React build, reverse-proxies
                       │              /api|/admin|/health to Django — production only)
        ┌──────────────┴──────────────┐
        ▼                             ▼
  React SPA (static)           Django / Gunicorn   (REST API, JWT auth, RBAC, throttling, audit middleware)
                                       │
                       ┌───────────────┼──────────────┐
                       ▼               ▼              ▼
                  PostgreSQL         Redis          Celery Worker
                  (isolated          (cache +            │
                   container)        Celery broker)      ▼
                                                     Celery Beat  (hourly appointment-reminder schedule)
```

Full write-up, including how local dev and the containerized production stack coexist in one
`docker-compose.yml`: [docs/architecture.md](docs/architecture.md).

## Tech Stack

**Backend** — Python, Django 6.1, Django REST Framework, PostgreSQL, Redis, Celery + Celery Beat,
JWT (`djangorestframework-simplejwt`) with token blacklisting, `drf-spectacular` (OpenAPI),
Argon2 password hashing, `pyotp` (TOTP 2FA), Gunicorn.

**Frontend** — React 19 + TypeScript + Vite, `react-router-dom`, `@tanstack/react-query`, `axios`
— no component library, hand-written CSS design system. See [docs/frontend.md](docs/frontend.md).

**AI** — a deterministic rule engine (no ML/LLM dependency), Ollama (local) and Groq (cloud) as
interchangeable LLM providers, a from-scratch keyword-scored RAG retriever (no vector DB —
the corpus is small and per-patient-scoped, so it wasn't warranted).

**Infrastructure** — Docker Compose, Nginx, Let's Encrypt/Certbot, Prometheus + Grafana +
cAdvisor + Flower (opt-in monitoring profile).

## AI Architecture

Three layers, only the first of which is fully implemented:

1. **Layer 1 — Rule engine** (`triage/rules_engine.py`) — keyword-matches free-text symptoms
   against a seeded `Symptom` catalog, sums severity weights, and applies threshold/red-flag
   logic to produce an urgency level and suggested department. **This is the authoritative
   layer** — it runs and returns a complete result even if the LLM is disabled or unreachable.
2. **Layer 2 — ML classifier** — **not implemented** (see [Limitations](#limitations)).
3. **Layer 3 — LLM summary** (`triage/llm.py` + `triage/tasks.py`) — takes the Layer 1 output and
   writes a short, plain-language explanation for the patient. Dual-provider (Ollama/Groq,
   switchable by an admin at runtime), and runs as a **background Celery task** so a slow or
   unreachable LLM never blocks the triage HTTP response.

The **AI patient assistant** (`ai_assistant/`) is a separate RAG feature reusing the same LLM
client: `User → Permission Check → Retriever (this patient's own data + hospital FAQs) → LLM →
Response`. The retriever only ever queries the authenticated patient's own related records — a
structural boundary, not a prompt instruction, so it can't be talked around by the question's
wording. This is verified on every `evaluate_ai` run, not just asserted once:

```
Patient A asks about Patient B  →  DENY   (verified: Patient B's data never enters the retrieved context)
Patient A asks about own data   →  ALLOW  (verified: Patient A's own data is present)
```

Full methodology and a checked-in example run: [docs/ai_evaluation.md](docs/ai_evaluation.md).

## Healthcare Workflow

```
Patient enters symptoms
        │
        ▼
Rule-based triage (urgency + department)  ──▶  LLM summary (background, explanatory only)
        │
        ▼
Patient books an appointment (real doctor, real availability-derived slots)
        │
        ▼
Receptionist can check the patient in  ──▶  Doctor sees them on today's queue
        │
        ▼
Doctor: medical record + diagnosis  ──▶  prescription  ──▶  lab test request (optional)
        │                                                        │
        ▼                                                        ▼
Billing: invoice + payment                              Lab Staff: sample → processing → report
        │                                                        │
        ▼                                                        ▼
Patient sees the visit's record, prescription, lab report, and invoice on their dashboard
```

## Security

- **Authentication** — JWT access/refresh with rotation and blacklisting on logout,
  logout-all-devices, 2FA (TOTP) with one-time recovery codes, email verification, password
  reset with automatic session invalidation.
- **Authorization** — role-based access control (Admin/Doctor/Patient/Receptionist/Lab Staff)
  plus object-level checks (a doctor can only review assessments tied to their own appointments;
  a patient can only ever see their own records) — see [docs/permissions.md](docs/permissions.md).
- **Rate limiting** — DRF throttling, with `NUM_PROXIES` correctly configured so `X-Forwarded-For`
  can't be spoofed to bypass it behind Nginx.
- **Audit logging** — every mutating request and login attempt is logged with who/what/when/
  from-where/which-object/what-changed — see [docs/permissions.md](docs/permissions.md#audit-trail).
- **Secrets** — the Groq API key is Fernet-encrypted at rest, derived from `DJANGO_SECRET_KEY`.
- **Passwords** — Argon2 hashing, minimum length 10.
- **Production hardening** — HSTS, secure + HttpOnly cookies, CSP, CORS with no default-trusted
  origins, `DEBUG=False`, explicit `ALLOWED_HOSTS`, SSL redirect.
- **File uploads** — extension- and size-validated (lab reports, message attachments).

Full detail: [docs/authentication.md](docs/authentication.md), [docs/permissions.md](docs/permissions.md).

## Database

PostgreSQL in production/Docker (SQLite for quick local runs), Redis for caching (departments,
doctor availability, AI provider settings — signal-invalidated) and as the Celery broker.

| App | Owns |
|---|---|
| `accounts` | Custom `User` (role-based), 2FA, recovery codes |
| `departments` | Hospital departments |
| `patients` / `doctors` | Role profiles (auto-created via signal), doctor availability/leave |
| `appointments` | Bookings, queue, waitlist, feedback |
| `medical_records` | Visit notes, diagnoses |
| `prescriptions` | Prescriptions + line items |
| `laboratory` | Lab test requests, reports |
| `billing` | Invoices, payments |
| `messaging` | Patient–doctor threads |
| `notifications` | In-app notifications |
| `triage` | Rule engine, AI provider settings, triage assessments, emergency guidance |
| `ai_assistant` | RAG assistant, hospital FAQs |
| `analytics` | Read-only aggregation for admin dashboards |
| `audit_logs` | Middleware-driven audit trail |
| `health` | Liveness + Prometheus metrics endpoints |

Full model reference: [project_blueprint/17_database_models.md](project_blueprint/17_database_models.md).

## API

- **Swagger UI**: `/api/docs/` (interactive — supports bearer-token "Authorize")
- **ReDoc**: `/api/redoc/`
- **OpenAPI schema**: `/api/schema/`
- Auth, request/response examples, error shapes, and pagination/filtering conventions:
  [docs/api.md](docs/api.md), [docs/authentication.md](docs/authentication.md).

## Installation

Requires Python 3.13+, Node 22+, and either Docker or a local PostgreSQL/Redis (SQLite works for
a quick backend-only run — Redis is optional too, falling back to LocMemCache).

```bash
git clone <this-repo>
cd "AI-Powered Healthcare Triage & Appointment System/main"

python -m venv .venv
. .venv/Scripts/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit as needed — see Environment Variables below
python manage.py migrate
python manage.py seed_demo      # optional but recommended — see Demo Accounts below
python manage.py runserver
```

Frontend (separate terminal):

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173, proxies /api to the Django dev server
```

## Environment Variables

All read via `.env` (see [.env.example](.env.example) for the full, current list):

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django's cryptographic signing key — also derives the Fernet key for the encrypted Groq API key |
| `DJANGO_DEBUG` | `True` for local dev; **must** be `False` in any real deployment |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames |
| `CORS_ALLOWED_ORIGINS` | Comma-separated trusted frontend origins (empty = none trusted) |
| `POSTGRES_DB` / `_USER` / `_PASSWORD` / `_HOST` / `_PORT` | Database connection (omit `POSTGRES_HOST` to fall back to SQLite) |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | Redis URLs for the task queue |
| `CELERY_TASK_ALWAYS_EAGER` | `True` runs Celery tasks synchronously (used in CI/tests) |
| `REDIS_CACHE_URL` | Redis URL for Django's cache backend (unset = LocMemCache) |
| `EMAIL_HOST_USER` / `_PASSWORD` / `_HOST_NAME` | SMTP for verification/reset emails (unset = console backend) |
| `DJANGO_LOG_LEVEL` | Root log level (`django.request`/`django.security` always log `WARNING`+ regardless) |
| `DOMAIN` / `EMAIL` | Production-only — Let's Encrypt/Certbot (`--profile production`) |
| `GRAFANA_ADMIN_USER` / `_PASSWORD`, `FLOWER_BASIC_AUTH` | Monitoring-only (`--profile monitoring`) |

The LLM provider (Ollama vs Groq), model names, timeout, and the Groq API key are **not** env
vars — they're admin-editable at runtime via `AIProviderSettings` (`/api/triage/ai-settings/`),
encrypted at rest and Redis-cached.

## Docker Setup

```bash
docker compose up                       # local dev: db + redis + web (host ports exposed via
                                         # docker-compose.override.yml, auto-merged)
docker compose --profile production up  # production: adds nginx (HTTPS) + certbot; no service
                                         # publishes a host port except nginx's 80/443
docker compose --profile monitoring up  # adds Prometheus + Grafana + cAdvisor + Flower
```

First production run needs `scripts/init-letsencrypt.sh` (bootstraps a dummy cert so nginx can
start before the real one is issued) — full walkthrough in
[docs/deployment.md](docs/deployment.md) and [docs/monitoring.md](docs/monitoring.md).

## Running Tests

```bash
python manage.py test
```

198 tests, all passing — authentication, appointments (slots/double-booking/waitlist/queue),
medical records/prescriptions/lab/billing/messaging, AI (rule engine matrix, LLM reliability
metrics, RAG authorization matrix), RBAC/object-level permissions/rate limiting/audit logging,
and the demo-seed command itself.

Frontend type-check: `cd frontend && node ./node_modules/typescript/bin/tsc -b`.

Lint/format (dev-only tooling, not in the production image — `pip install -r requirements-dev.txt`):

```bash
python -m ruff check .
python -m black --check .
```

Full pipeline (lint, tests, security scan, migration check, Docker build) runs on every push/PR —
see [docs/cicd.md](docs/cicd.md).

## Demo Accounts

```bash
python manage.py seed_demo
```

Creates one account per role — password **`Demo@12345`** for all of them — plus a connected
clinical workflow (appointments, records, prescriptions, lab tests, invoices, messages,
notifications, AI examples) to explore immediately instead of clicking through empty screens.
Idempotent, safe to re-run. Full account list and what gets seeded:
[docs/demo.md](docs/demo.md).

## Screenshots

Not yet captured — planned for the demo-video pass (see the roadmap's Phase 18). This section
will be filled in then rather than with placeholders now.

## Project Structure

```
main/
├── accounts/ departments/ patients/ doctors/ appointments/
├── medical_records/ prescriptions/ laboratory/ billing/ messaging/
├── notifications/ triage/ ai_assistant/ analytics/ audit_logs/ health/
├── ai_healthcare_triage_appointment_system/   # settings, urls, celery app
├── frontend/                                  # React + TypeScript + Vite SPA
├── nginx/                                     # reverse-proxy config templates
├── monitoring/                                # Prometheus/Grafana provisioning
├── scripts/                                   # init-letsencrypt.sh, backup/restore
├── docs/                                      # this project's own written documentation
├── project_blueprint/                         # original design docs + phase-by-phase roadmap
├── docker-compose.yml / docker-compose.override.yml / Dockerfile
├── requirements.txt / .env.example
└── manage.py
```

## Limitations

- **The ML classifier (Layer 2 of the AI architecture) is not implemented.** No validated
  clinical dataset exists to train one responsibly, and shipping an unvalidated symptom
  classifier in a healthcare context is a worse outcome than not having one. The deterministic
  rule engine (Layer 1) is authoritative and doesn't depend on it.
- **No real payment gateway is integrated.** Billing supports invoices and payment *records*
  (cash/card/bank transfer/other), but doesn't process an actual card/online transaction —
  intentionally out of scope for this project's purpose.
- **This is not a medical diagnosis system.** Every triage output — rule-based urgency, LLM
  summary, and department suggestion — is preliminary decision support only, and carries that
  disclaimer everywhere it's shown. It does not replace evaluation by a qualified healthcare
  professional, and red-flag/emergency results explicitly say to seek immediate care rather than
  wait for an appointment.

## Future Enhancements

Tracked in [project_blueprint/21_roadmap_phase5_to_20.md](project_blueprint/21_roadmap_phase5_to_20.md):
a final security/architecture review pass, a recorded demo walkthrough, and the GitHub portfolio
release polish (screenshots, architecture diagrams, deployment URL). CI/CD hardening and
automated backup/restore verification are already done — see [docs/cicd.md](docs/cicd.md) and
[docs/backups.md](docs/backups.md).
