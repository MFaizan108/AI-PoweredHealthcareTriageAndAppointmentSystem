#!/usr/bin/env bash
# One-time bootstrap for HTTPS via Let's Encrypt. Run this ONCE on the actual production host,
# after DNS for $DOMAIN already points at that host's public IP and docker-compose.yml's `nginx`
# service is reachable on ports 80/443.
#
# Why this exists: the nginx config (nginx/templates/default.conf.template) references a cert
# under /etc/letsencrypt/live/$DOMAIN/, so nginx can't even start until *some* cert exists there.
# This script creates a throwaway self-signed cert first so nginx can boot and serve the ACME
# HTTP-01 challenge, then requests the real certbot cert against that running nginx, then reloads
# nginx to pick it up. Safe to re-run (e.g. to switch domains) — it always regenerates from scratch.
#
# Usage: DOMAIN=example.com EMAIL=admin@example.com ./scripts/init-letsencrypt.sh
set -euo pipefail

: "${DOMAIN:?Set DOMAIN, e.g. DOMAIN=example.com}"
: "${EMAIL:?Set EMAIL, e.g. EMAIL=admin@example.com}"
STAGING="${STAGING:-0}"   # set STAGING=1 first to test against Let's Encrypt's staging rate limits

cd "$(dirname "$0")/.."

COMPOSE="docker compose"
CERTBOT_CONF_PATH="/etc/letsencrypt"

echo "### Creating a dummy certificate for $DOMAIN so nginx can start ..."
$COMPOSE run --rm --entrypoint "\
  mkdir -p $CERTBOT_CONF_PATH/live/$DOMAIN && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout '$CERTBOT_CONF_PATH/live/$DOMAIN/privkey.pem' \
    -out '$CERTBOT_CONF_PATH/live/$DOMAIN/fullchain.pem' \
    -subj '/CN=localhost'" certbot

echo "### Starting nginx ..."
$COMPOSE --profile production up -d nginx

echo "### Deleting the dummy certificate ..."
$COMPOSE run --rm --entrypoint "\
  rm -rf $CERTBOT_CONF_PATH/live/$DOMAIN && \
  rm -rf $CERTBOT_CONF_PATH/archive/$DOMAIN && \
  rm -rf $CERTBOT_CONF_PATH/renewal/$DOMAIN.conf" certbot

echo "### Requesting the real Let's Encrypt certificate for $DOMAIN ..."
STAGING_ARG=""
if [ "$STAGING" != "0" ]; then STAGING_ARG="--staging"; fi

$COMPOSE run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $STAGING_ARG \
    --email '$EMAIL' -d '$DOMAIN' \
    --rsa-key-size 2048 --agree-tos --no-eff-email --non-interactive" certbot

echo "### Reloading nginx with the real certificate ..."
$COMPOSE exec nginx nginx -s reload

echo "### Done. $DOMAIN is now served over HTTPS."
echo "### certbot's own container handles renewal (see the 'certbot' service's entrypoint loop);"
echo "### nginx must be reloaded after each renewal — cron this if not already handled."
