# Monitoring & Observability

## Health endpoints

Plain Django views (not DRF) — deliberately bypass JWT auth and the anon rate throttle entirely,
since load balancers/uptime monitors hit these unauthenticated and often (see
`health/views.py`).

| Endpoint | Checks | 200 vs 503 |
|---|---|---|
| `GET /health/` | DB + cache + Celery, aggregated | 200 only if all three are healthy |
| `GET /health/db/` | `SELECT 1` against the default database | |
| `GET /health/redis/` | Round-trips a value through `CACHES['default']` (Redis in production; Django's in-process `LocMemCache` in local dev/CI when `REDIS_CACHE_URL` is unset — either way, "healthy" means the configured cache backend actually works) | |
| `GET /health/celery/` | `CELERY_TASK_ALWAYS_EAGER=True`: always healthy (no broker/worker involved). Otherwise: `control.inspect().ping()` against the broker — unhealthy if no worker responds | |

`/health/` response shape:
```json
{ "api": "healthy", "database": "healthy", "redis": "healthy", "celery": "healthy" }
```
Each check function (`health/checks.py`) catches broadly and returns `(False, "<error detail>")`
rather than letting an exception 500 the endpoint — a health check that itself crashes is worse
than useless for a monitor trying to page someone.

## Metrics

`GET /metrics` (`health/metrics.py`) exposes Prometheus-format counters/histograms via
`prometheus_client` directly — **not** the `django-prometheus` package, which as of this writing
pins `Django<6.1` and would silently downgrade the project off 6.1 (breaking the built-in CSP
middleware several Phase 8 fixes depend on) the moment it's installed. A single middleware
(`health.metrics.PrometheusMiddleware`, first in `MIDDLEWARE` so it wraps every other middleware's
overhead too) records:

- `django_http_requests_total{method, view, status}` — request count by status code, i.e. error rate
- `django_http_request_duration_seconds{method, view}` — request latency histogram, i.e. API response time

`view` is the URL name (`resolver_match.view_name`), not the raw path — `/api/patients/7/` and
`/api/patients/42/` collapse into one low-cardinality series instead of one per patient ID.

**Never exposed publicly**: nginx explicitly returns `404` for `/metrics`
(`nginx/templates/default.conf.template`) — Prometheus reaches it over the internal Docker network
directly (`web:8000/metrics`), which never goes through nginx at all.

## The monitoring stack (Prometheus + Grafana + cAdvisor + Flower)

Opt-in via `--profile monitoring` (independent of `--profile production` — it can equally point at
a local dev stack for testing the dashboards themselves):
```
docker compose --profile monitoring up -d
```
or, for a full production deploy with monitoring:
```
docker compose -f docker-compose.yml --profile production --profile monitoring up -d
```

| Service | Role | Access |
|---|---|---|
| `prometheus` | Scrapes `web:8000/metrics` (API latency/error-rate) and `cadvisor:8080/metrics` (per-container CPU/RAM/disk/network) every 15s | Internal only in prod; `:9090` published in dev (`docker-compose.override.yml`) |
| `cadvisor` | Per-container resource metrics — covers the roadmap's "CPU, RAM, Disk" for every service (web, db, redis, celery workers) | Internal only in prod; `:8080` published in dev |
| `grafana` | Dashboards, pre-provisioned with the Prometheus datasource and a starter "Healthcare API Overview" dashboard (request rate, 5xx rate, p95 latency, container CPU/mem/disk — `monitoring/grafana/provisioning/`) | `:3000`, always published — protected by its own login (`GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD`, no default password) |
| `flower` | Celery-specific dashboard — task success/failure counts, queue depth, per-worker status. A separate concern from the Prometheus/Grafana metrics stack (task-level detail Prometheus doesn't have) | `:5555`, protected by HTTP basic auth (`FLOWER_BASIC_AUTH=user:password`, required) |

**Required env vars for this profile** (no insecure defaults — see `.env.example`):
`GRAFANA_ADMIN_PASSWORD`, `FLOWER_BASIC_AUTH`.

Neither Grafana nor Flower sit behind nginx in this phase — they're published directly on their
own ports, protected by their own auth. Restricting them further (firewall/VPN/nginx
basic-auth-proxy) is a reasonable hardening step for a real deployment but isn't built here, to
keep this phase's scope to what the roadmap actually asked for.

## What's *not* built here

Sentry-style exception aggregation/alerting isn't part of this phase — Phase 9's stdout logging
(`LOGGING` in `settings.py`) plus Prometheus's error-rate metric cover "what broke and how often";
wiring actual alerts (Alertmanager, PagerDuty, etc.) on top of these metrics is future work beyond
what the roadmap specifies for this phase.
