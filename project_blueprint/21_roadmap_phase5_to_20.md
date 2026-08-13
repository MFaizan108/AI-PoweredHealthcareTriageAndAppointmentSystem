# Roadmap: Phase 5 → Phase 20 (Post-Backend Roadmap)

> Status: **Planning / reference only — not started unless explicitly instructed phase-by-phase.**
> This extends [20_roadmap_phases.md](20_roadmap_phases.md). Phases 1–4 (Core, Healthcare, AI, Production) plus the blueprint gap-analysis round are already implemented. Everything below is the roadmap for what comes *after* the backend.

---

## Phase 5 — API Documentation & Developer Experience 📖

**Status: ✅ Implemented (2026-08-11)** — `drf-spectacular` wired up, `/docs/` folder written, 38/38 tests still passing.

**Goal:** Project ko kisi doosre developer ke liye understandable banana.

**Features**
- OpenAPI schema
- Swagger UI
- ReDoc
- Authentication documentation
- All endpoint descriptions
- Request/response examples
- Error-response documentation
- Role/permission documentation
- Pagination/filter documentation
- API versioning strategy

**Deliverables**
```
/docs/
├── api.md
├── architecture.md
├── authentication.md
└── permissions.md
```
Plus live endpoints:
- `/api/schema/`
- `/api/docs/`
- `/api/redoc/`

---

## Phase 6 — Testing Expansion & Quality Assurance 🧪

**Status: ✅ Implemented (2026-08-12)** — 38 → 142 tests, all passing. Found and fixed 6 real bugs along the way (see conversation/commit history): a `DoctorLeave`/`DoctorAvailability` create-ownership gap, unfiltered clinical-record queryset leaks to receptionist/lab_staff/other roles in medical_records/prescriptions/laboratory/appointments/triage, a broken doctor-review permission check on the triage `review` action, an audit-log middleware bug that failed to attribute non-JSON login attempts, and missing `ordering` on several models causing nondeterministic pagination.

Abhi 38/38 tests hain. Is phase ka target sirf number barhana nahi, balkay critical workflows ko comprehensively test karna hai.

**Authentication**
- Registration
- Login
- Logout
- Refresh token
- Blacklisted token
- Email verification
- Password reset
- 2FA

**Appointments**
- Slot generation
- Double booking
- Cancellation
- Rescheduling
- Waitlist
- Queue
- Doctor leave

**Healthcare**
- Medical records
- Prescriptions
- Lab reports
- Billing
- Messaging

**AI**
- Red flag → Emergency
- High
- Moderate
- Low
- No-match
- LLM failure (Ollama)
- LLM failure (Groq)
- RAG permissions

**Security**
- RBAC
- Object-level permissions
- Rate limiting
- Audit logging
- Unauthorized access

**Target:** 70–100+ meaningful tests, not artificially inflated tests.

---

## Phase 7 — Performance & Scalability ⚡

**Status: ✅ Implemented (2026-08-12)** — DB indexes + N+1 fixes, Redis caching (departments/doctor-availability/AI-provider-settings) with signal-based invalidation, async triage AI summary via Celery, `CONN_MAX_AGE`, and a locust load-test harness. Found and fixed a genuinely broken password hasher (Argon2 migration — see report) and an IP-throttle-bypass gap (`NUM_PROXIES`). 150/150 tests passing.

Ab system ko load ke under test karo.

**Database**
- `select_related`
- `prefetch_related`
- Proper indexes
- Query optimization
- N+1 query detection

**Redis**
- Cache departments
- Cache doctor availability
- Cache frequently accessed data
- Cache invalidation strategy

**Celery** — move heavy operations into background jobs where appropriate:
- LLM calls
- Email
- PDF generation
- Reports
- Notifications
- Reminders

**Load Testing** — test with 50 / 100 / 500 / 1000 users, especially on:
- `/api/appointments/`
- `/api/triage/`
- `/api/triage/assistant/`

---

## Phase 8 — Advanced Security Audit 🔐

**Status: ✅ Implemented (2026-08-12)** — 2FA recovery codes, logout-all-devices + auto session-kill on password reset, CORS (safe default: no origins trusted), CSP, file-upload validation, stronger password policy, and audit-log object/change tracking. 174/174 tests passing.

Healthcare project ke liye ye must-have phase hai.

**Authentication**
- JWT rotation
- Refresh-token expiry
- 2FA recovery strategy
- Session invalidation

**API**
- CORS review
- CSRF review
- Rate limits
- Permission audit
- Object-level authorization

**Data**
- Sensitive field encryption
- Secret management
- Password policy
- Secure file handling

**Production**
- HSTS
- CSP
- Secure cookies
- HTTPS
- Security headers
- `DEBUG=False`
- Proper `ALLOWED_HOSTS`

**Audit — verify:**
- Who?
- What?
- When?
- From where?
- Which object?
- What changed?

---

## Phase 9 — Production Deployment 🐳

**Status: ✅ Implemented (2026-08-12)** — Nginx reverse proxy + HTTPS via Let's Encrypt (certbot,
dummy-cert bootstrap script), a prod-safe `docker-compose.yml` (no host ports for db/redis/web —
nginx is the only public entrypoint) with all local-dev host-port mappings moved into an
auto-merged `docker-compose.override.yml`, stdout-based structured logging, static/media served
directly by nginx from shared volumes, and manual DB backup/restore scripts. 174/174 tests still
passing. See [docs/deployment.md](../docs/deployment.md).

Ab local Docker stack ko real deployment mein le jao.

**Architecture**
```
                    Internet
                       │
                       ▼
                    Nginx
                       │
                       ▼
                 Django / Gunicorn
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   PostgreSQL        Redis          Celery
                                      │
                                      ▼
                                   Celery Beat
```

**Deployment**
- Docker Compose production
- Nginx
- Gunicorn
- PostgreSQL
- Redis
- Celery Worker
- Celery Beat
- HTTPS
- Domain
- Environment variables
- Backups
- Static files
- Media files
- Logging

---

## Phase 10 — Monitoring & Observability 📈

**Status: ✅ Implemented (2026-08-12)** — `/health/`, `/health/db/`, `/health/redis/`,
`/health/celery/` (plain Django views, no auth/throttle, never crash — always return clean
healthy/unhealthy JSON); a hand-rolled `prometheus_client` `/metrics` endpoint (request
count-by-status + latency histogram, i.e. error rate + API response time) rather than the
`django-prometheus` package, which pins `Django<6.1` and would have downgraded the project;
Prometheus + Grafana (pre-provisioned dashboard) + cAdvisor (per-container CPU/RAM/disk) + Flower
(Celery task/worker dashboard) as an opt-in `--profile monitoring` compose stack. `/metrics`
blocked at the nginx layer (Prometheus reaches it over the internal network only). 183/183 tests
passing. See [docs/monitoring.md](../docs/monitoring.md).

Production mein sirf deploy karna enough nahi.

**Logging**
- Application errors
- API errors
- Celery failures
- Authentication failures
- AI failures

**Monitoring — track:**
- CPU
- RAM
- Disk
- Database
- Redis
- Celery
- API response time
- Error rate

**Health endpoints**
- `/health/`
- `/health/db/`
- `/health/redis/`
- `/health/celery/`

Example response:
```json
{
  "api": "healthy",
  "database": "healthy",
  "redis": "healthy",
  "celery": "healthy"
}
```

---

## Phase 11 — Frontend / Professional Dashboards 🎨

**Status: ✅ Implemented (2026-08-12)** — React 19 + TypeScript + Vite SPA (`frontend/`), auth
(login incl. 2FA/recovery-code, register), and all five role dashboards: Patient, Doctor,
Receptionist, Lab Staff, Admin. Production served by the same nginx that terminates TLS
(`frontend/Dockerfile`, multi-stage build). Verified end-to-end in real headless-browser runs
against the live backend — a full chained workflow across all five roles (Doctor sets availability
→ Receptionist registers a walk-in patient and books them → Doctor treats them → Lab Staff
processes and delivers the report → Admin creates the staff accounts and reviews
analytics/audit-logs) completed with zero console/network errors on the final run. Added a
self-service Doctor Availability page beyond the original section list — without it a new doctor
account is permanently unbookable, a real functional gap rather than scope creep. Several real
bugs found and fixed along the way (invalid `<div>`-in-`<p>` HTML nesting in the triage AI-summary
pending state; `getAvailableSlots()` not deduping across overlapping `DoctorAvailability` windows).
See [docs/frontend.md](../docs/frontend.md).

Ab backend ko proper UI do.

**Patient Dashboard**
```
├── Appointments
├── AI Triage
├── Medical Records
├── Prescriptions
├── Lab Reports
├── Billing
├── Messages
└── Notifications
```

**Doctor Dashboard**
```
├── Today's Queue
├── Appointments
├── Patients
├── Medical Records
├── Prescriptions
├── Lab Requests
├── Messages
└── Analytics
```

**Receptionist Dashboard**
```
├── Queue
├── Walk-in Registration
├── Patient Search
├── Appointments
└── Check-in
```

**Lab Staff Dashboard**
```
├── Pending Tests
├── Processing
├── Reports
└── Upload Report
```

**Admin Dashboard**
```
├── Users
├── Doctors
├── Patients
├── Departments
├── Appointments
├── Billing
├── AI Analytics
├── Audit Logs
└── System Settings
```

---

## Phase 12 — AI Evaluation & Safety 🤖

**Status: ✅ Implemented (2026-08-13)** — a new `python manage.py evaluate_ai` command runs all
three evaluation layers and produces a Markdown report: a named rule-engine test matrix (Red
Flag/High/Moderate/Low/Unknown, 100% accuracy against the canonical seeded symptom set), live
LLM latency/failure/timeout/invalid-response metrics per provider (Ollama vs Groq, via a new
`ask_llm(..., settings_obj=...)` override that probes a provider without touching the admin's
persisted config), and a full-stack RAG authorization matrix (Patient A asks about Patient B ->
DENY, Patient A asks about own data -> ALLOW) driven through the real `/api/ai-assistant/ask/`
endpoint inside a transaction that's always rolled back. Found and fixed a real bug on the first
live run: outside `manage.py test`, DRF's `APIClient` was rejected by the `ALLOWED_HOSTS` check
(Django's test-environment setup normally patches that in, but a plain command process doesn't
get it for free) — fixed with a scoped `override_settings`. 193/193 tests passing (+10 for the
evaluation harness itself). See [docs/ai_evaluation.md](../docs/ai_evaluation.md) and the
checked-in example run at [docs/ai_evaluation_report.md](../docs/ai_evaluation_report.md).

Particularly important phase for this project. Ab AI ko sirf "working" prove nahi karna; evaluate karna hai.

**Rule Engine Evaluation** — create test cases:
- Red Flag → Emergency
- High Severity → High
- Multiple Moderate → Moderate
- Low Severity → Low
- Unknown → Safe fallback

**LLM Evaluation — measure:**
- Response latency
- Failure rate
- Timeout rate
- Invalid response rate
- Provider comparison (Ollama vs Groq)

**RAG Evaluation — test:**
```
Patient A asks about Patient B
        ↓
       DENY
```
```
Patient A asks about own appointment
        ↓
       ALLOW
```

**Most important: RAG must never bypass authorization.**

---

## Phase 13 — Demo / Seed Environment 🧑‍💻

**Status: ✅ Implemented (2026-08-13)** — `python manage.py seed_demo` creates one account per
role (admin/3 doctors across different departments/receptionist/lab staff/3 patients, password
`Demo@12345` for all), each demo doctor gets a real Mon–Fri availability schedule (so they're
actually bookable — closing the same gap Phase 11 found), and a connected clinical workflow:
appointments (past+upcoming), medical records with diagnoses, prescriptions, lab tests (one
completed, one pending), invoices/payments, a message exchange, notifications, and two AI
examples (real rule-engine triage assessments + a RAG assistant query log). Idempotent — safe to
re-run, verified by running it twice and confirming zero duplicate rows; passwords are set via
`create_user()` specifically because a plain `get_or_create()` on the User model would silently
store them in plaintext. 198/198 tests passing (+5 for the seed command itself, including an
actual login through `/api/accounts/login/` to prove the hashed password really works). See
[docs/demo.md](../docs/demo.md).

Ek command se complete demo system ready ho:
```
python manage.py seed_demo
```

**Creates**
- Admin, Doctor, Patient, Receptionist, Lab Staff
- Departments
- Appointments
- Medical Records
- Prescriptions
- Lab Tests
- Notifications
- Invoices
- Messages
- AI examples

**Then**
```
docker compose up
python manage.py migrate
python manage.py seed_demo
```
Aur project immediately explore ho sake.

---

## Phase 14 — Documentation 📚

**Status: ✅ Implemented (2026-08-13)** — a top-level `README.md` covering every section below,
written from the actual current state of the project (env vars cross-checked against
`settings.py`/`.env.example`, test count verified by running the suite, Python/Node versions
verified against the venv and CI config) rather than aspirational copy. Fixed a forward-reference
placeholder in `docs/architecture.md` that had pointed at this README before it existed. No
Screenshots yet — deliberately left as "not yet captured, see Phase 18" rather than filled with
placeholder images.

Professional README.

**README structure**
```
# AI Healthcare Triage & Appointment System

## Overview
## Features
## Architecture
## Tech Stack
## AI Architecture
## Healthcare Workflow
## Security
## Database
## API
## Installation
## Environment Variables
## Docker Setup
## Running Tests
## Demo Accounts
## Screenshots
## Project Structure
## Limitations
## Future Enhancements
```

**Especially the Limitations section must state (transparency strengthens the project):**
- ML classifier not implemented due to lack of validated clinical dataset
- Real payment gateway optional/not integrated
- AI is not a medical diagnosis system

---

## Phase 15 — CI/CD Finalization ⚙️

**Status: ✅ Implemented (2026-08-13)** — `ci.yml` split into staged jobs (lint-backend,
lint-frontend, backend-tests, frontend-build, security, docker-build) so a fast lint failure
doesn't wait on slow test services. Added `ruff` + `black` (backend), reusing the already-wired
`oxlint` + added `npm audit` (frontend), `pip-audit`, a migration-check step, and a Docker build
verification for both `Dockerfile` and `frontend/Dockerfile` (built locally first to confirm
before trusting the workflow YAML). Turning on ruff/black required an actual one-time cleanup
pass first — 13 real ruff findings fixed (unused imports, import order) and 88 files reformatted
by black — re-verified with a full test-suite run afterward (198/198, unchanged) to confirm the
formatting pass was purely cosmetic. Deploy is deliberately **not** automated: no real deployment
target/secrets exist for this repo, and fabricating them would be worse than being explicit that
production deploy stays the manual `docker compose --profile production up` from Phase 9 for now.
See [docs/cicd.md](../docs/cicd.md).

Current GitHub Actions ko upgrade karo:
```
Push
 ↓
Lint
 ↓
Unit Tests
 ↓
Integration Tests
 ↓
Security Checks
 ↓
Build Docker Image
 ↓
Deploy
```

**Add**
- Ruff/Flake8
- Black
- pytest/Django tests
- pip-audit
- Docker build
- Migration check

---

## Phase 16 — Production Backup & Recovery 💾

**Status: ✅ Implemented (2026-08-13)** — `scripts/backup_verify.sh` implements the literal
test-restore cycle (PostgreSQL → Backup → Delete test DB → Restore → Verify) against a disposable
scratch database, never the real one; validated against the live dev database (dumped, restored
into a scratch DB, confirmed exact row counts matched, dropped the scratch DB) before being
documented as trustworthy. Added `scripts/backup_media.sh`/`restore_media.sh` for the
`media_data` volume (lab report uploads, message attachments) alongside the existing DB
scripts — deliberately **not** backing up prescription PDFs as files, since they're generated on
demand from DB rows (`prescriptions/pdf.py`) and never stored, so there's nothing there a file
backup would add. Automation is a documented host crontab (daily backup, weekly verify-drill) —
not a bespoke scheduler container, since this project is a single-host `docker compose`
deployment with no existing scheduling infra to hook a new container into, and cron calling the
already-tested scripts is simpler than inventing and debugging a new always-running service for
the same job. See [docs/backups.md](../docs/backups.md).

Healthcare data ke liye critical.

**Database — automatic:**
- Daily backup
- Weekly backup
- Test restore cycle:
```
PostgreSQL
 ↓
Backup
 ↓
Delete test DB
 ↓
Restore
 ↓
Verify
```

**Files**
- Lab reports / prescription PDFs ke backups.

---

## Phase 17 — Final Security & Architecture Review 🔍

**Status: ✅ Implemented (2026-08-13)** — full audit across every area below; found and fixed
four real issues: **[HIGH]** lab reports/message attachments were served completely
unauthenticated via a raw `/media/` nginx location (any URL, once seen, worked forever for
anyone — PHI with no real access control) — replaced with authenticated download endpoints
reusing each resource's existing permission rule, and removed the nginx `/media/` location
entirely; **[MEDIUM]** the audit log's `X-Forwarded-For` parsing trusted the first (client-
spoofable) hop instead of the last (nginx-appended, trustworthy) one, undermining the audit
trail's "From where?" column; **[MEDIUM]** the AI-triage and AI-assistant endpoints had no
tighter throttle than generic CRUD despite triggering real LLM cost/compute; **[MEDIUM]** Django
admin's own login form completely bypassed 2FA, letting any account — including a superuser —
into `/admin/` with just a password. 198 → 218 tests (+20 for these fixes, including a real
headless-browser verification of the media-file fix). See
[docs/security_review.md](../docs/security_review.md) for full detail on each finding and what
was checked and found already solid.

Ek complete audit — is phase mein **new feature nahi, sirf weaknesses identify/fix karo**:
```
Authentication       ✅
Authorization        ✅
Database             ✅
API                  ✅
Files                ✅
AI                   ✅
Secrets              ✅
Docker               ✅
Production config    ✅
Logging              ✅
Backups              ✅
```

---

## Phase 18 — Final Demo & Presentation 🎥

Project ka professional demo video:

| Scene | Content |
|---|---|
| 1 | Patient registration/login |
| 2 | AI triage: Symptoms → Emergency → Department → Explanation |
| 3 | Appointment booking |
| 4 | Doctor dashboard |
| 5 | Medical record + prescription |
| 6 | Lab test → report |
| 7 | Billing |
| 8 | Messaging |
| 9 | Admin analytics |
| 10 | Security / architecture |

---

## Phase 19 — GitHub Portfolio Release 🚀

Repository ko professional banao:
```
ai-healthcare-triage-system/
│
├── accounts/
├── appointments/
├── doctors/
├── patients/
├── medical_records/
├── prescriptions/
├── laboratory/
├── triage/
├── ai_assistant/
├── billing/
├── messaging/
├── analytics/
├── notifications/
├── audit_logs/
│
├── project_blueprint/
├── tests/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── README.md
└── LICENSE
```

**Add**
- Screenshots
- Architecture diagram
- API docs
- Test results
- Demo video
- Deployment URL

---

## Phase 20 — CV / LinkedIn / Final Release 🏆

Final project ko CV mein feature dump ki tarah nahi likhna — focus:

**Stack**
> Python · Django · DRF · PostgreSQL · Redis · Celery · Docker · JWT · TOTP · Ollama · Groq

**Engineering**
> RBAC · Async Tasks · Audit Logging · Rate Limiting · CI/CD · Automated Testing

**AI**
> Rule-Based Triage · LLM Summarization · RAG · Permission-Aware AI Assistant

**Result**
> 38+ automated tests → eventually final verified count

---

## 🗺️ Full Roadmap (Current → Phase 20)

```
CURRENT
Phase 1–4 + Blueprint Gap-Analysis Round
           │
           ▼
05  API Documentation
           │
           ▼
06  Testing Expansion
           │
           ▼
07  Performance
           │
           ▼
08  Security Audit
           │
           ▼
09  Production Deployment
           │
           ▼
10  Monitoring
           │
           ▼
11  Professional Dashboards
           │
           ▼
12  AI Evaluation
           │
           ▼
13  Demo Environment
           │
           ▼
14  Documentation
           │
           ▼
15  CI/CD
           │
           ▼
16  Backup & Recovery
           │
           ▼
17  Final Audit
           │
           ▼
18  Demo Video
           │
           ▼
19  GitHub Release
           │
           ▼
20  CV / LinkedIn / Portfolio
```
