#!/bin/sh
# Run a command once a day at a fixed UTC hour, forever (used by the scheduler
# containers in docker-compose.prod.yml instead of a host crontab).
#   Usage: daily.sh <utc-hour 0-23> <command> [args...]
#   RUN_ON_START=1 also runs the command once when the container starts.
# A failed run is logged and retried the next day; the loop never exits on it.
set -u

HOUR="${1:?pass the UTC hour (0-23)}"
shift
[ "$#" -gt 0 ] || { echo "daily.sh: pass the command to run" >&2; exit 2; }
case "$HOUR" in
  ''|*[!0-9]*) echo "daily.sh: hour must be 0-23, got '$HOUR'" >&2; exit 2 ;;
esac
[ "$HOUR" -le 23 ] || { echo "daily.sh: hour must be 0-23, got '$HOUR'" >&2; exit 2; }

run() {
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start: $*"
  if "$@"; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) done"
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) FAILED (exit $?), will retry tomorrow" >&2
  fi
}

seconds_until_next_run() {
  now=$(( $(date -u +%-H) * 3600 + $(date -u +%-M) * 60 + $(date -u +%-S) ))
  wait=$(( HOUR * 3600 - now ))
  [ "$wait" -gt 0 ] || wait=$(( wait + 86400 ))
  echo "$wait"
}

[ "${RUN_ON_START:-0}" = "1" ] && run "$@"

while true; do
  wait=$(seconds_until_next_run)
  echo "next run in ${wait}s (daily at ${HOUR}:00 UTC)"
  sleep "$wait"
  run "$@"
done
