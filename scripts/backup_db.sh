#!/usr/bin/env sh
# Nightly PostgreSQL backup for the production stack, with retention.
# Usage (cron, from the project root):
#   0 2 * * * ./scripts/backup_db.sh >> backups/backup.log 2>&1
set -eu

BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.production"
STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="$BACKUP_DIR/school_saas-$STAMP.dump"

mkdir -p "$BACKUP_DIR"
# Custom format: compressed and restorable with pg_restore.
$COMPOSE exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$FILE"
test -s "$FILE"
echo "$(date -Iseconds) backup written: $FILE"

# Retention: only files this script created, older than KEEP_DAYS.
find "$BACKUP_DIR" -maxdepth 1 -name 'school_saas-*.dump' -mtime +"$KEEP_DAYS" -exec rm -f {} \;
# Copy BACKUP_DIR off the server (object storage or another host) after each run.
