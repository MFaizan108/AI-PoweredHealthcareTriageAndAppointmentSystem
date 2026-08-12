# Deployment

## Two ways this project runs Docker

| | Local dev | Production |
|---|---|---|
| Command | `docker compose up -d db redis` (Django itself via `manage.py runserver` on the host) | `docker compose -f docker-compose.yml --profile production up -d` |
| `db`/`redis`/`web` host ports | Published (`docker-compose.override.yml`, auto-merged) | **Not published** — only reachable inside the Docker network |
| Public entrypoint | none (localhost only) | `nginx` service (ports 80/443) |
| `DEBUG` | `True` | `False` |

`docker-compose.yml` alone is production-safe: nothing in it publishes a host port for `db`,
`redis`, or `web`, and `nginx`/`certbot` only start when `--profile production` is passed. Plain
`docker compose up` (no flags) auto-merges `docker-compose.override.yml`, which adds back the
host-port mappings local dev has always used (`5434`, `6381`, `8000`) — this is why the existing
day-to-day workflow (`docker compose up -d db redis` + host-side `manage.py`) keeps working
unchanged. A real deployment should explicitly pass `-f docker-compose.yml` to skip that override.

## First-time production setup

1. Provision a Linux host (any VPS/cloud VM) with Docker + the Compose plugin installed, and point
   the domain's DNS **A record** at its public IP. HTTPS issuance in step 4 will fail until this
   resolves.
2. Copy `.env.example` to `.env` and fill in real values — see
   [Environment variables](#environment-variables) below. Generate a fresh `DJANGO_SECRET_KEY`
   (never reuse the dev one), a strong `POSTGRES_PASSWORD`, and set `DOMAIN`/`EMAIL`.
3. Build and start everything except the public-facing pieces first, so migrations/collectstatic
   run and the app is healthy before it's ever exposed:
   ```
   docker compose -f docker-compose.yml up -d db redis web celery_worker celery_beat
   docker compose -f docker-compose.yml logs -f web   # confirm migrate + collectstatic succeeded
   ```
4. Bootstrap HTTPS (one-time; see the script's own comments for exactly what it does):
   ```
   DOMAIN=yourdomain.com EMAIL=admin@yourdomain.com ./scripts/init-letsencrypt.sh
   ```
   This starts `nginx` as a side effect. From here on, redeploys are just:
   ```
   docker compose -f docker-compose.yml --profile production up -d --build
   ```
5. Create the admin account: `docker compose exec web python manage.py createsuperuser`.

## Domain

`DJANGO_ALLOWED_HOSTS` and `DOMAIN` must both be set to the real domain (no scheme, no trailing
slash — e.g. `yourdomain.com`, not `https://yourdomain.com/`). `DOMAIN` feeds the nginx config
(`nginx/templates/default.conf.template`, rendered via the official nginx image's built-in
`envsubst` templating at container start) and the certbot cert request.

## HTTPS / Let's Encrypt

`scripts/init-letsencrypt.sh` implements the standard certbot+nginx bootstrap: nginx's config
always references a cert at `/etc/letsencrypt/live/$DOMAIN/`, so a throwaway self-signed cert is
generated first (letting nginx start and serve the ACME HTTP-01 challenge), then the real
certificate is requested against that running nginx, then nginx is reloaded — no downtime, no
manual cert file wrangling. The `certbot` service (started by `--profile production`) runs
`certbot renew` on a 12-hour loop in the background for the lifetime of the container; nginx still
needs a reload after a renewal actually replaces a cert (renewal only happens ~30 days before
expiry, so this is infrequent — cron an `nginx -s reload` on the host, or watch for it manually).

`STAGING=1` is available on the init script to test against Let's Encrypt's staging environment
first (much higher rate limits, but the browser will show an untrusted cert) before requesting a
real one.

## Environment variables

| Variable | Required in prod | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | ✅ | Long random value, never the dev default |
| `DJANGO_DEBUG` | ✅ (`False`) | Enables HSTS/secure-cookies/SSL-redirect — see `settings.py`'s `if not DEBUG:` block |
| `DJANGO_ALLOWED_HOSTS` | ✅ | Comma-separated, must include `DOMAIN` |
| `DJANGO_LOG_LEVEL` | – | Defaults `INFO`; `django.request`/`django.security` always log at `WARNING`+ regardless |
| `CORS_ALLOWED_ORIGINS` | once a frontend exists | Comma-separated, never wildcarded (JWTs are bearer tokens) |
| `POSTGRES_DB`/`_USER`/`_PASSWORD` | ✅ | `_HOST`/`_PORT` are fixed to `db`/`5432` inside `docker-compose.yml` |
| `CELERY_BROKER_URL`/`_RESULT_BACKEND`/`REDIS_CACHE_URL` | fixed by compose | Point at the `redis` service, different DB indices |
| `EMAIL_HOST_USER`/`_PASSWORD`/`_NAME` | for real email | Falls back to console-backend (logs only) if unset |
| `DOMAIN` | ✅ (production profile) | Feeds nginx + certbot — see above |
| `EMAIL` | ✅ (production profile, init script only) | Let's Encrypt account/expiry-notice email |

## Frontend

The `nginx` service builds from `frontend/Dockerfile` (not the stock `nginx` image) — a two-stage
build that compiles the React app (`npm run build`) and bakes the static output into the nginx
image alongside the templated proxy config. There's no separate frontend container/service: one
nginx serves the compiled SPA *and* terminates TLS *and* reverse-proxies `/api`, `/admin`,
`/health` to Django. See [frontend.md](frontend.md).

## Static & media files

Django's `collectstatic` (run automatically by `web`'s startup command) writes into the
`static_data` named volume; the `nginx` service mounts that same volume read-only and serves
`/static/*` directly — Gunicorn never touches static-file requests in production. `media_data`
(lab report/attachment uploads) works the same way for `/media/*`. Both get `expires`/no-access-log
treatment in the nginx config since they're immutable or access-controlled-elsewhere content.

## Logging

Everything logs to stdout/stderr (`LOGGING` in `settings.py`, Gunicorn's `--access-logfile -
--error-logfile -`) rather than to files inside the container — the standard 12-factor approach, so
log storage/rotation/shipping is `docker logs` / the host's log driver's job, not the app's. See
[architecture.md](architecture.md) for what's logged where; Phase 10 builds actual
monitoring/alerting on top of this.

## Backups

`scripts/backup_db.sh` / `scripts/restore_db.sh` — manual `pg_dump`/`psql` wrappers against the
`db` container, gzip-compressed, timestamped, with age-based pruning. This is the basic mechanism
only; Phase 16 adds a scheduled cadence and a test-restore verification cycle. Run a restore drill
on a scratch database before trusting a backup in an actual incident.

## Zero-downtime notes

`web`/`celery_worker`/`celery_beat` all run `restart: unless-stopped`, so a host reboot or crashed
container self-heals. A redeploy (`--build` + `up -d`) currently causes a brief `web` restart
(migrations + collectstatic run again on the new container before Gunicorn starts) — acceptable at
this project's scale; a blue/green or rolling-restart setup is future work, not in this phase's
scope.
