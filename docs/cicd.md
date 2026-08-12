# CI/CD

`.github/workflows/ci.yml` runs on every push/PR to `main`. Six jobs, staged so a fast failure
(lint) doesn't wait on the slow ones (tests, Docker builds), and the Actions UI shows exactly
which stage broke:

```
push
  ├─▶ lint-backend   (ruff + black --check)
  │     └─▶ backend-tests   (Django system check, migration check, full test suite)
  │           └─▶ security   (pip-audit, Django deploy security checklist)
  │
  └─▶ lint-frontend  (oxlint, npm audit)
        └─▶ frontend-build  (tsc -b + vite build)

docker-build  (needs backend-tests + frontend-build — builds both images, no push)
```

## Lint

- **Backend** — `ruff check .` (import order + common correctness lints — `E`/`F`/`W`/`I`, line
  length left to Black) and `black --check .`. Config lives in `pyproject.toml`.
- **Frontend** — `oxlint` (already wired up in Phase 11) plus `npm audit --omit=dev`.

Both tools required a one-time pass to actually apply: `ruff --fix` cleared 13 import-order/
unused-import findings, and `black .` reformatted 88 files (whitespace/wrapping only — verified
with a full test-suite run afterward that nothing behavioral changed). Without that pass, turning
these on in CI would have failed on the very next commit for reasons unrelated to whatever anyone
was actually working on.

## Tests

`backend-tests` adds one step ahead of the existing test run: `manage.py makemigrations --check
--dry-run`, so a model change committed without its migration fails CI instead of surfacing as a
runtime `OperationalError` in whoever pulls next. `frontend-build` runs the same `tsc -b && vite
build` used to verify the SPA locally.

There's deliberately no separate "integration tests" job — this project doesn't distinguish unit
from integration tests structurally; `manage.py test` already runs everything from pure rule-engine
unit tests (`triage/tests.py`) through full-stack `APIClient`-driven request/response tests
(most of the suite) in one pass, which is what "integration" means here in practice.

## Security

- **`pip-audit -r requirements.txt`** — scans for known CVEs in pinned dependencies. Clean as of
  this phase.
- **`manage.py check --deploy`** — Django's built-in production-readiness checklist (HSTS, secure
  cookies, `DEBUG`, `SECRET_KEY` strength, ...). Run with a throwaway `DJANGO_SECRET_KEY` and
  `DJANGO_DEBUG=False`, since it's static analysis of `settings.py`, not a real boot — the
  throwaway key trips one expected `SECRET_KEY looks auto-generated` **warning**, which is
  non-fatal (the command only exits non-zero on an ERROR-level finding, verified locally with a
  properly-random key: zero issues).

`requirements-dev.txt` (`-r requirements.txt` plus `ruff`/`black`/`pip-audit`) keeps these tools
out of the production image — `Dockerfile` still installs only `requirements.txt`.

## Docker build

Builds both `Dockerfile` (backend) and `frontend/Dockerfile` (nginx + built SPA) — verified
locally before wiring into CI, since a syntax-valid workflow doesn't guarantee the referenced
Dockerfiles still build after a dependency bump. No registry push — there's nowhere configured to
push *to* yet (see Deploy, below).

## Deploy — intentionally not automated yet

The roadmap's target pipeline shape ends in Deploy. This repo doesn't have a deployment target
(server, cloud account, or registry) with CI-accessible credentials, so an automated CD job here
would either do nothing real or need invented secrets — both worse than being explicit that this
step is manual for now:

```
docker compose --profile production up -d
```

on a host you control, per [deployment.md](deployment.md). Wiring real CD (e.g. SSH-deploy over
Actions, or a registry push + remote `docker compose pull && up -d`) is a follow-up once an actual
target exists — tracked alongside the rest of [the roadmap](../project_blueprint/21_roadmap_phase5_to_20.md).
