# Test Results

```
python manage.py test
```
```
Ran 218 tests in 149.254s

OK
```

218/218 passing, run locally against SQLite + `CELERY_TASK_ALWAYS_EAGER=True` (the same
Postgres-optional fallback CI uses — see [cicd.md](cicd.md)) on 2026-08-13, immediately before the
Phase 19 portfolio pass. The same suite runs against real PostgreSQL/Redis in `docker compose`
dev and in `backend-tests` in CI, so this isn't a SQLite-only result — see
[docs/cicd.md](cicd.md) for the CI job that runs it against Postgres on every push/PR.

## By app

Grown from 38 (Phase 5) to 142 (Phase 6) to 150 (Phase 7) to 174 (Phase 8) to 198 (Phases
13–16) to 218 (Phase 17) — each phase's report in this `docs/` folder and in
[project_blueprint/21_roadmap_phase5_to_20.md](../project_blueprint/21_roadmap_phase5_to_20.md)
says what was added and, where relevant, what real bug the new tests caught.

| App | Tests | Covers |
|---|---:|---|
| `accounts` | 36 | Registration, login, JWT rotation/blacklisting, logout-all, 2FA + recovery codes, email verification, password reset, admin-login 2FA enforcement |
| `triage` | 31 | Rule engine matrix (red-flag/high/moderate/low/unknown), LLM summary task, AI provider settings, AI-evaluation harness, throttling |
| `laboratory` | 22 | Lab test requests, report upload/status transitions, object-level access, authenticated report download |
| `appointments` | 20 | Slot generation, double-booking prevention, cancellation/rescheduling, waitlist, queue, doctor leave |
| `audit_logs` | 13 | Middleware attribution, redacted body capture, `X-Forwarded-For` trust boundary (spoofed vs. trusted hop) |
| `doctors` | 13 | Availability windows, leave, ownership checks |
| `ai_assistant` | 12 | RAG retriever scoping, authorization matrix (Patient A can never retrieve Patient B's data), evaluation harness |
| `departments` | 12 | CRUD + read-only access for non-admin roles |
| `messaging` | 10 | Thread scoping to a shared appointment, authenticated attachment download |
| `medical_records` | 9 | Visit notes/diagnoses, role-scoped querysets |
| `health` | 9 | `/health/*` liveness endpoints, `/metrics` |
| `prescriptions` | 8 | Multi-item prescriptions, PDF export |
| `billing` | 6 | Invoices, partial/full payment tracking |
| `patients` | 6 | Profile auto-creation, patient-only access |
| `analytics` | 6 | Aggregate endpoints, admin-only access |
| `notifications` | 5 | Internal creation from other apps, read/unread |
| **Total** | **218** | |

## What's deliberately not chased

- **Coverage-percentage tooling** (`coverage.py` + a badge) isn't wired up. The 218 tests are
  scenario-driven (see each phase's report for what was specifically targeted — auth flows,
  double-booking, RBAC boundaries, AI authorization, rate limits), not written to hit a coverage
  number, and a percentage badge would imply a rigor this project doesn't claim. If that becomes
  useful later it's a small addition (`coverage run manage.py test && coverage report`), not a
  redesign.
- **Frontend automated tests**: there's no Jest/Vitest/RTL suite in `frontend/`. Frontend
  correctness in this project comes from real headless-browser runs against the live backend at
  the end of Phases 11, 17, and 18 (see [frontend.md](frontend.md) and
  [demo_script.md](demo_script.md)) — TypeScript's own type-check (`tsc -b`, run in CI) plus those
  driven runs, rather than a parallel unit-test suite for a UI this size.
