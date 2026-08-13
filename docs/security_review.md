# Final Security & Architecture Review

Phase 17 of the roadmap, deliberately scoped as an audit-and-fix pass — no new features, only
weaknesses identified and closed. Covers every area the roadmap calls out: Authentication,
Authorization, Database, API, Files, AI, Secrets, Docker, Production config, Logging, Backups.

Most of that surface was already hardened by earlier phases (Argon2 hashing, JWT rotation +
blacklisting, RBAC + object-level permissions across every clinical app, encrypted secrets at
rest, CSP/HSTS/secure cookies, audit logging, rate limiting, validated file uploads, backup
verification). This review's job was to find what earlier phases *missed*. It found four real
issues, all now fixed and covered by tests.

## Findings

### 1. [HIGH] Lab reports and message attachments were publicly reachable, unauthenticated

**The gap:** `LabReport.report_file` and `Message.attachment` are Django `FileField`s. The
serializers exposed their raw `MEDIA_URL` path (e.g. `/media/lab_reports/2026/08/report.pdf`) in
API responses, and both local Django (`DEBUG=True`) and production nginx
(`location /media/ { alias /app/media/; }`) served that path with **zero access control** —
no login, no permission check, nothing. Once a URL was seen once (in a legitimately-authorized
API response, a browser's network log, a shared screenshot), it worked forever for anyone,
completely bypassing every RBAC/object-level permission this project otherwise enforces
carefully. For a healthcare system, that's PHI (lab results) with no real access control.

**The fix:**
- New authenticated download endpoints — `GET /api/lab/reports/<id>/download/`
  (`laboratory.views.LabReportDownloadView`) and `GET /api/messages/<id>/attachment/`
  (`messaging.views.MessageAttachmentDownloadView`) — each reusing the *exact same* access rule
  as the resource itself (`_check_lab_access` / sender-recipient-admin), so there's one source of
  truth for "who can see this," not two.
- Serializers now return that endpoint's relative path instead of the raw media path
  (`to_representation()` override), so the response shape is unchanged for callers.
- **Removed the nginx `/media/` location entirely** and dropped the `media_data` volume mount
  from the nginx service — it no longer needs, and no longer has, filesystem access to files it
  never serves. Production media now only reaches a client through Django's own permission check.
- Frontend: a plain `<a href={report_file}>` can't carry a JWT (this API is bearer-token-only, no
  session cookies) — `download.tsx`'s `openAuthenticatedFile()` fetches the file through the same
  authenticated axios instance every other call uses, then opens it as a blob URL. Verified in a
  real browser (not just unit tests): logged in as a demo patient, clicked "View report file,"
  confirmed the opened tab is a `blob:` URL (proving it went through the authenticated fetch, not
  a direct media link) with zero console/network errors.
- Tests: 7 cases in `laboratory/tests.py` (`LabReportDownloadTests`), 5 in `messaging/tests.py`
  (`MessageAttachmentDownloadTests`) — unauthenticated rejected, owner/participant allowed,
  outsider rejected, admin/lab-staff always allowed, missing file → 404, and the serializer
  actually returns the new endpoint path rather than a `/media/` path.

### 2. [MEDIUM] Audit-log IP addresses were trivially spoofable

**The gap:** `audit_logs.middleware._client_ip()` took the *first* entry of
`X-Forwarded-For`. Nginx's `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for` (correct
config) *appends* the real client address rather than replacing the header — so the trustworthy
value is always the *last* hop nginx itself added, and everything before that is whatever the
client sent. Trusting the first entry meant any client could put an arbitrary fake IP into the
audit trail (and their own login-history page, `accounts.views.LoginHistoryView`, which reads
straight from this same table) just by sending their own `X-Forwarded-For: 6.6.6.6` header —
undermining the "From where?" column of the exact audit trail Phase 8 built for accountability.

**The fix:** `_client_ip()` now mirrors DRF's own `SimpleRateThrottle.get_ident()` logic exactly
— reads `rest_framework.settings.api_settings.NUM_PROXIES` (already correctly `0` in dev, `1` in
production behind the one nginx hop) and trusts only the last `NUM_PROXIES` entries. Same trust
boundary the rate limiter already used; the audit log just wasn't using it.

**Tests:** two new cases in `audit_logs/tests.py` — with `NUM_PROXIES=1`, a spoofed prefix
(`6.6.6.6, 9.9.9.9`) resolves to `9.9.9.9` (the hop nginx actually appended), never `6.6.6.6`;
with `NUM_PROXIES=0` (dev), `X-Forwarded-For` is ignored entirely.

### 3. [MEDIUM] AI-calling endpoints shared the generic rate limit

**The gap:** `POST /api/triage/assess/` (with `use_ai_summary=True`, the default) and
`POST /api/ai-assistant/ask/` each trigger a real LLM call — local Ollama compute, or a
paid/rate-limited Groq API request. Both only had the generic `120/minute` per-user throttle,
which is fine for CRUD but lets a single account (even patient-role) burn LLM cost/compute far
faster than any legitimate usage pattern needs.

**The fix:** a new `"ai": "20/hour"` throttle scope (`DEFAULT_THROTTLE_RATES`) and
`triage.throttles.AIRateThrottle`, applied to both endpoints via `throttle_classes` **and**
`throttle_scope` (DRF's `ScopedRateThrottle` reads `view.throttle_scope`, not an attribute on the
throttle class itself — easy to set only one and have it silently do nothing, which is exactly
what happened on the first pass here before the tests caught it). Applies uniformly rather than
only when `use_ai_summary` is true, trading a little strictness for a throttle that can't be
skipped by a malformed request body.

**Tests:** one case per endpoint, patching `AIRateThrottle.get_rate()` to a low rate for a fast,
deterministic test (`SimpleRateThrottle.THROTTLE_RATES` is snapshotted from
`api_settings.DEFAULT_THROTTLE_RATES` at import time, so `override_settings` alone can't lower it
mid-test — documented in the test comments so the next person doesn't hit the same dead end).

### 4. [MEDIUM] Django admin login completely bypassed 2FA

**The gap:** 2FA (TOTP) is enforced by `CustomTokenObtainPairSerializer` on the app's own JWT
login — but Django's built-in `/admin/` site has its own, completely separate login form
(`AdminAuthenticationForm`) that only ever checks username/password. Any account with 2FA enabled
— including a superuser — could log into `/admin/` (full model-level access, including editing
`AIProviderSettings`'s encrypted Groq key) with just a password, silently skipping the second
factor entirely.

**The fix:** `accounts.admin_forms.TwoFactorAdminAuthenticationForm` extends
`AdminAuthenticationForm` with an `otp_code` field, validated against `user.otp_secret` in
`clean()` whenever `user.is_2fa_enabled`. Wired in via `admin.site.login_form` in
`AccountsConfig.ready()`. Django's stock `admin/login.html` hardcodes only username/password
fields (doesn't loop over the form), so a small template override
(`templates/admin/login.html`) was needed to actually render the new field —
`TEMPLATES[0]['DIRS']` now points at a project-level `templates/` directory for exactly this one
override.

**Tests:** `accounts/tests_admin_2fa.py` — an account without 2FA logs in with password only; an
account with 2FA is rejected with password only; a valid TOTP code succeeds; an invalid one is
rejected. Drives the actual Django test `Client` against `/admin/login/`, not a mocked form.

## What was checked and found already solid

- **Authentication** — JWT rotation/blacklisting, 2FA recovery codes, password-reset session
  invalidation (`blacklist_all_outstanding_tokens`), email-verification token expiry (signed,
  24h), enumeration-safe password-reset responses.
- **Authorization** — every clinical app (`medical_records`, `prescriptions`, `laboratory`,
  `billing`, `messaging`, `triage`) follows the same `_check_clinical_access`-style pattern:
  patient sees only their own (read-only), treating doctor sees only their own patients, admin
  sees everything, other roles excluded by default. Checked all nine `permissions.py` files for
  consistency, not just spot-checked a few.
- **Secrets** — `.env`/`db.sqlite3` confirmed never committed (`git ls-files` clean),
  `.dockerignore` excludes them from the build context, Groq API key Fernet-encrypted at rest.
- **AI / prompt injection** — the RAG assistant's authorization boundary is structural, not
  prompt-based (see [ai_evaluation.md](ai_evaluation.md)): the retriever only ever queries the
  authenticated patient's own related objects, so even a maximally successful prompt-injection
  attempt has nothing to exfiltrate beyond what was already retrieved before the LLM ever saw the
  question.
- **Docker** — non-root `appuser` in the backend image, `.dockerignore` keeps secrets/dev
  artifacts out of the build context, prod compose publishes no host port except nginx's 80/443.
- **Production config / Logging** — `DEBUG=False` hardening block, HSTS/secure
  cookies/CSP/`NUM_PROXIES` all correct, sensitive fields (`password`, `otp_secret`,
  `groq_api_key`, tokens, ...) redacted in audit-log request bodies at any nesting depth.
- **Backups** — Phase 16's `backup_verify.sh` test-restore cycle re-reviewed, still sound.

## Verification

- 218 tests passing (198 → 218: +20 for this phase's four fixes), `ruff`/`black` clean.
- Fix 1 additionally verified in a real headless-browser run (not just backend unit tests) —
  see above.
- The one live-environment hiccup during this phase (Docker Desktop going down mid-review,
  taking the local Postgres/Redis dev containers with it) was diagnosed, not worked around
  silently: confirmed all 218 tests still pass against SQLite + LocMemCache (matching how CI
  already runs), isolating the failures to the unrelated infrastructure outage rather than
  papering over a possible real regression.
