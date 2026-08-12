#!/usr/bin/env bash
# Restores a backup produced by backup_media.sh into the running `web` container's media volume.
# DESTRUCTIVE: wipes the current contents of /app/media first. Always confirms interactively.
#
# Usage: ./scripts/restore_media.sh backups/media_20260101T000000Z.tar.gz
set -euo pipefail

cd "$(dirname "$0")/.."

BACKUP_FILE="${1:?Usage: $0 <path-to-media-backup.tar.gz>}"
[ -f "$BACKUP_FILE" ] || { echo "No such file: $BACKUP_FILE" >&2; exit 1; }

echo "!!! This will DELETE everything currently in the media volume (/app/media), then restore from:"
echo "    $BACKUP_FILE"
read -r -p "Type 'restore' to confirm: " CONFIRM
if [ "$CONFIRM" != "restore" ]; then
    echo "Aborted."
    exit 1
fi

echo "### Clearing current /app/media contents ..."
docker compose exec -T web sh -c 'find /app/media -mindepth 1 -delete'

echo "### Extracting backup into /app/media ..."
docker compose exec -T web mkdir -p /app/media
cat "$BACKUP_FILE" | docker compose exec -T web tar xzf - -C /app/media

echo "### Done."
