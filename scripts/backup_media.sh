#!/usr/bin/env bash
# Manual/cron-able backup of uploaded files (lab reports, message attachments — the media_data
# volume). Prescription PDFs are NOT included here on purpose: they're generated on demand from
# Prescription/PrescriptionItem rows (see prescriptions/pdf.py), never stored as files, so the
# database backup already covers them — regenerable anytime, nothing to back up separately.
#
# Usage: ./scripts/backup_media.sh   (tars the `web` container's /app/media via docker compose exec)
set -euo pipefail

cd "$(dirname "$0")/.."

KEEP_DAYS="${KEEP_DAYS:-14}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_FILE="$BACKUP_DIR/media_${TIMESTAMP}.tar.gz"

echo "### Archiving /app/media from the web container ..."
docker compose exec -T web tar czf - -C /app/media . > "$OUT_FILE"

echo "### Wrote $OUT_FILE ($(du -h "$OUT_FILE" | cut -f1))"

echo "### Pruning media backups older than $KEEP_DAYS days ..."
find "$BACKUP_DIR" -name "media_*.tar.gz" -mtime "+$KEEP_DAYS" -print -delete

echo "### Done."
