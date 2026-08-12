#!/usr/bin/env bash
# Restores a backup produced by backup_db.sh into the running `db` container.
# DESTRUCTIVE: drops and recreates the target database first. Always confirms interactively.
#
# Usage: ./scripts/restore_db.sh backups/healthcare_triage_20260101T000000Z.sql.gz
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_FILE="${1:?Usage: $0 <path-to-backup.sql.gz>}"
[ -f "$BACKUP_FILE" ] || { echo "No such file: $BACKUP_FILE" >&2; exit 1; }

POSTGRES_DB="${POSTGRES_DB:-healthcare_triage}"
POSTGRES_USER="${POSTGRES_USER:-healthcare_admin}"

echo "!!! This will DROP and recreate '$POSTGRES_DB' in the db container, then restore from:"
echo "    $BACKUP_FILE"
read -r -p "Type the database name ('$POSTGRES_DB') to confirm: " CONFIRM
if [ "$CONFIRM" != "$POSTGRES_DB" ]; then
    echo "Aborted."
    exit 1
fi

echo "### Terminating existing connections and recreating $POSTGRES_DB ..."
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();"
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS \"$POSTGRES_DB\";"
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$POSTGRES_DB\";"

echo "### Restoring ..."
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

echo "### Done. Restart the web/celery services so any pooled connections pick up the fresh data."
