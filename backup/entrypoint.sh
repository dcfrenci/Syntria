#!/bin/sh
set -u
trap 'exit 0' TERM INT

while true; do
  /usr/local/bin/backup.sh || {
    echo "[backup] FAILED at $(date -u +%FT%TZ)" >&2
    [ -z "${HEALTHCHECK_URL:-}" ] || wget -q -O /dev/null -T 10 "${HEALTHCHECK_URL%/}/fail" || true
  }
  sleep $(( ${BACKUP_INTERVAL_HOURS:-24} * 3600 )) &
  wait $!
done