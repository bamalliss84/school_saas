#!/usr/bin/env sh
# Restore a backup made by backup_db.sh. This REPLACES the current database contents.
# Usage: ./scripts/restore_db.sh backups/school_saas-YYYYMMDD-HHMMSS.dump
set -eu
FILE="${1:?pass the .dump file to restore}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.production"
printf 'This overwrites the production database with %s. Type RESTORE to continue: ' "$FILE"
read -r answer
[ "$answer" = "RESTORE" ] || { echo "Cancelled."; exit 1; }
$COMPOSE stop backend
$COMPOSE exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < "$FILE"
$COMPOSE start backend
echo "Restore finished."
