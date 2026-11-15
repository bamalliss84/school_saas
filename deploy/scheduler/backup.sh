#!/bin/sh
# One backup run inside the "backup" container: database dump + media archive,
# then retention. Connection settings come from PG* variables (see compose).
# Files go to /backups (bind-mounted to ./backups on the host); copy that folder
# off the server after each run, a backup on the same server is not enough.
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
DB_FILE="$BACKUP_DIR/school_saas-$STAMP.dump"
MEDIA_FILE="$BACKUP_DIR/media-$STAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

# Custom format: compressed and restorable with scripts/restore_db.sh.
# Written to a temporary name first so a failed dump never looks like a backup.
pg_dump -Fc -f "$DB_FILE.partial"
test -s "$DB_FILE.partial"
mv "$DB_FILE.partial" "$DB_FILE"
echo "database backup written: $DB_FILE"

if [ -d /media-src ]; then
  tar -czf "$MEDIA_FILE.partial" -C /media-src .
  mv "$MEDIA_FILE.partial" "$MEDIA_FILE"
  echo "media backup written: $MEDIA_FILE"
fi

# Retention: only files this job created, older than KEEP_DAYS.
find "$BACKUP_DIR" -maxdepth 1 \( -name 'school_saas-*.dump' -o -name 'media-*.tar.gz' \) \
  -mtime +"$KEEP_DAYS" -exec rm -f {} \;
find "$BACKUP_DIR" -maxdepth 1 -name '*.partial' -mmin +60 -exec rm -f {} \;
