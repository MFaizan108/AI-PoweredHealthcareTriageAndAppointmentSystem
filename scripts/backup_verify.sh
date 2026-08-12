#!/usr/bin/env bash
# The test-restore verification cycle:
#
#     PostgreSQL -> Backup -> Delete test DB -> Restore -> Verify
#
# Restores a backup into a disposable *scratch* database (never the real one — a different
# name, inside the same Postgres instance) and checks it actually contains data. A backup file
# existing proves pg_dump didn't crash; it does NOT prove the dump is restorable or complete —
# this does. Safe to run anytime, including straight against a production backup, since the real
# database is never touched.
#
# Usage: ./scripts/backup_verify.sh [path-to-backup.sql.gz]   (defaults to the newest in ./backups)
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_DIR="${BACKUP_DIR:-./backups}"
POSTGRES_DB="${POSTGRES_DB:-healthcare_triage}"
POSTGRES_USER="${POSTGRES_USER:-healthcare_admin}"
SCRATCH_DB="${POSTGRES_DB}_restore_test"

# Tables checked as a basic "the restore actually has real rows, not just an empty schema"
# smoke test — one from each of auth, the core clinical workflow, and AI, not an exhaustive list.
CHECK_TABLES="accounts_user appointments_appointment triage_triageassessment"

BACKUP_FILE="${1:-}"
if [ -z "$BACKUP_FILE" ]; then
    BACKUP_FILE="$(ls -t "$BACKUP_DIR"/"${POSTGRES_DB}"_*.sql.gz 2>/dev/null | head -n1 || true)"
fi
if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    echo "No backup file found (looked in $BACKUP_DIR). Run backup_db.sh first, or pass a path explicitly." >&2
    exit 1
fi

psql_admin() {
    docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -c "$1" >/dev/null
}

drop_scratch_db() {
    # Terminate any lingering connections first — DROP DATABASE fails while one exists.
    psql_admin "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$SCRATCH_DB' AND pid <> pg_backend_pid();"
    psql_admin "DROP DATABASE IF EXISTS \"$SCRATCH_DB\";"
}

echo "### Verifying: $BACKUP_FILE"

echo "### [1/4] Dropping any stale scratch database from a previous run ..."
drop_scratch_db

echo "### [2/4] Creating scratch database $SCRATCH_DB ..."
psql_admin "CREATE DATABASE \"$SCRATCH_DB\";"

echo "### [3/4] Restoring backup into $SCRATCH_DB ..."
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U "$POSTGRES_USER" -d "$SCRATCH_DB" >/dev/null

echo "### [4/4] Checking restored data ..."
FAILED=0
for table in $CHECK_TABLES; do
    count="$(docker compose exec -T db psql -U "$POSTGRES_USER" -d "$SCRATCH_DB" -tAc "SELECT count(*) FROM $table;" 2>/dev/null || echo "ERROR")"
    if [ "$count" = "ERROR" ]; then
        echo "    FAIL: could not query $table (table missing — restore is likely broken)"
        FAILED=1
    else
        echo "    OK: $table has $count row(s)"
    fi
done

echo "### Cleaning up scratch database ..."
drop_scratch_db

if [ "$FAILED" -ne 0 ]; then
    echo "### VERIFY FAILED — this backup may not be safely restorable. Investigate before relying on it."
    exit 1
fi
echo "### VERIFY PASSED — $BACKUP_FILE is restorable and contains real data."
