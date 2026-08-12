# Backups & Recovery

A backup file existing proves nothing on its own — it proves `pg_dump` didn't crash. The only
thing that actually matters for a healthcare project is whether a backup is *restorable*, which
is why this page leads with the verification cycle, not the dump command.

## Scripts

| Script | What it does |
|---|---|
| `scripts/backup_db.sh` | `pg_dump`s the database, gzip-compressed, timestamped, into `./backups/`. Prunes anything older than `KEEP_DAYS` (default 14). |
| `scripts/backup_media.sh` | Tars the `media_data` volume (lab report uploads, message attachments) via the running `web` container. Same timestamping/pruning. |
| `scripts/backup_verify.sh` | **The test-restore cycle.** Restores the newest (or a given) backup into a disposable scratch database, checks it actually has rows in it, then drops the scratch database. Never touches the real database — safe to run anytime, including directly against a production backup. |
| `scripts/restore_db.sh` | Restores a backup into the **real** database. Destructive (drops and recreates it first) — interactive confirmation required. Only for an actual incident, not routine verification. |
| `scripts/restore_media.sh` | Same, for a media backup — interactive confirmation required. |

All of them wrap `docker compose exec` against the running `db`/`web` services, matching how
this project is actually deployed (see [deployment.md](deployment.md)) — no separate backup
infrastructure, no credentials beyond what's already in `.env`.

## The test-restore cycle

```
PostgreSQL
    │
    ▼
  Backup            (scripts/backup_db.sh)
    │
    ▼
Delete test DB       (drops any stale healthcare_triage_restore_test from a previous run)
    │
    ▼
  Restore            (into that scratch database — never the real one)
    │
    ▼
  Verify             (row counts on accounts_user / appointments_appointment /
    │                 triage_triageassessment — a broken or truncated dump fails here)
    ▼
Delete test DB       (cleanup — the scratch database never lingers)
```

Run it manually anytime:

```bash
./scripts/backup_db.sh
./scripts/backup_verify.sh
```

Validated against a live, populated database before being wired into automation: dumped the real
dev database (27 users, 8 appointments, 4 triage assessments at the time), restored it into a
scratch database, confirmed those exact counts came back, then dropped the scratch database —
the row counts matching exactly is what "verified", not just "the script exited 0".

## Recommended schedule (cron)

This project runs as a single-host `docker compose` deployment (see
[deployment.md](deployment.md)) — no cloud scheduler exists to hook into, so cron on the host is
the automation mechanism, not a bespoke scheduler container. Add to the deploying user's
crontab (`crontab -e`) on the production host:

```cron
# AI Healthcare Triage & Appointment System — backups
# Daily database + media backup at 02:00
0 2 * * * cd /path/to/main && ./scripts/backup_db.sh >> /var/log/healthcare-backup.log 2>&1
5 2 * * * cd /path/to/main && ./scripts/backup_media.sh >> /var/log/healthcare-backup.log 2>&1

# Weekly restore-verify drill, Sunday 03:00 — the thing that actually proves the daily
# backups are usable, not just that pg_dump ran without error
0 3 * * 0 cd /path/to/main && ./scripts/backup_verify.sh >> /var/log/healthcare-backup.log 2>&1
```

A "weekly backup" distinct from the daily one would just be a second, identical `pg_dump` —
`KEEP_DAYS=14` on the daily job already keeps two weeks of history, so the weekly slot is spent
on verification instead, which is the check that's actually missing without it. Adjust
`KEEP_DAYS` (env var on either backup script) if longer retention is wanted.

## What's covered, what isn't

- **Database** — everything: users, appointments, medical records, prescriptions, lab test
  *records*, billing, messages, notifications, triage assessments, audit logs.
- **Uploaded files** (`media_data`) — lab report files, message attachments. Backed up
  separately since they live outside Postgres.
- **Prescription PDFs are not backed up as files, on purpose** — they're generated on demand
  from `Prescription`/`PrescriptionItem` rows (`prescriptions/pdf.py`) and never written to
  disk. The database backup already covers the data they're rendered from; there's no file that
  needs its own backup.
- **Not covered**: anything outside the `db`/`media_data` volumes — application code and config
  live in git, not in a runtime backup's scope.

## Restoring for a real incident

```bash
./scripts/restore_db.sh backups/healthcare_triage_<timestamp>.sql.gz
./scripts/restore_media.sh backups/media_<timestamp>.tar.gz
```

Both require typing a confirmation phrase — there is no `--yes`/non-interactive flag, on purpose.
Restart `web`/`celery_worker`/`celery_beat` afterward so pooled DB connections pick up the fresh
data (`CONN_MAX_AGE=60` in `settings.py` means an old connection could otherwise serve stale
results for up to a minute).
