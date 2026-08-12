#!/usr/bin/env bash
# Manual/cron-able Postgres backup. Dumps the `db` container's database to a gzip-compressed,
# timestamped file under ./backups/ and prunes anything older than KEEP_DAYS.
#
# Run on a schedule via cron (see docs/backups.md for the recommended daily/weekly crontab
# lines) and verify what it actually produces with ./scripts/backup_verify.sh — a backup file
# existing proves pg_dump didn't crash, not that it's restorable.
#
# Usage: ./scripts/backup_db.sh   (reads POSTGRES_DB/POSTGRES_USER from .env via docker compose)
set -euo pipefail

cd "$(dirname "$0")/.."

KEEP_DAYS="${KEEP_DAYS:-14}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

POSTGRES_DB="${POSTGRES_DB:-healthcare_triage}"
POSTGRES_USER="${POSTGRES_USER:-healthcare_admin}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_FILE="$BACKUP_DIR/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

echo "### Dumping $POSTGRES_DB from the db container ..."
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$OUT_FILE"

echo "### Wrote $OUT_FILE ($(du -h "$OUT_FILE" | cut -f1))"

echo "### Pruning backups older than $KEEP_DAYS days ..."
find "$BACKUP_DIR" -name "${POSTGRES_DB}_*.sql.gz" -mtime "+$KEEP_DAYS" -print -delete

echo "### Done."
