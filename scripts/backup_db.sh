#!/usr/bin/env bash
# Manual/cron-able Postgres backup. Dumps the `db` container's database to a gzip-compressed,
# timestamped file under ./backups/ and prunes anything older than KEEP_DAYS.
#
# This is the basic mechanism only — see project_blueprint/21_roadmap_phase5_to_20.md Phase 16 for
# the planned scheduled daily/weekly cadence and the test-restore verification cycle.
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
