#!/bin/sh
set -eu

DIR=/backups
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
TS="$(date -u +%Y%m%d-%H%M%S)"
BASE="$DIR/syntria-$TS.sql.gz"
WORK="$DIR/.work-$TS"
trap 'rm -f "$WORK.sql" "$WORK.sql.gz"' EXIT

export PGPASSWORD="$POSTGRES_PASSWORD"

if [ -z "${AGE_RECIPIENT:-}" ] && [ "${ALLOW_PLAINTEXT_BACKUP:-false}" != "true" ]; then
  echo "[backup] AGE_RECIPIENT not set: refusing to write a plaintext dump (ALLOW_PLAINTEXT_BACKUP=true to override)" >&2
  exit 1
fi

echo "[backup] dumping $POSTGRES_DB"
pg_dump -h db -p "${POSTGRES_PORT:-5432}" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --no-owner --no-acl --clean --if-exists > "$WORK.sql"
gzip -9 "$WORK.sql"
gzip -t "$WORK.sql.gz"                                   # integrity check
[ "$(wc -c < "$WORK.sql.gz")" -gt 1024 ] || { echo "[backup] dump suspiciously small" >&2; exit 1; }

if [ -n "${AGE_RECIPIENT:-}" ]; then
  age -r "$AGE_RECIPIENT" -o "$BASE.age" "$WORK.sql.gz"
  FINAL="$BASE.age"
else
  mv "$WORK.sql.gz" "$BASE"
  FINAL="$BASE"
fi
chmod 600 "$FINAL"
echo "[backup] wrote $FINAL"

# local retention
find "$DIR" -maxdepth 1 -name 'syntria-*' -mtime +"$KEEP_DAYS" -delete

# optional off-site copy (encrypted only)
if [ -n "${RCLONE_REMOTE:-}" ]; then
  if [ -z "${AGE_RECIPIENT:-}" ]; then
    echo "[backup] refusing to upload an unencrypted backup: set AGE_RECIPIENT" >&2
    exit 1
  fi
  rclone copy "$FINAL" "$RCLONE_REMOTE"
  # --drive-use-trash=false: otherwise deleted dumps sit in Drive's trash and eat quota
  rclone delete "$RCLONE_REMOTE" --min-age "${KEEP_DAYS}d" --drive-use-trash=false
  echo "[backup] uploaded to $RCLONE_REMOTE"
fi

# dead-man's switch: only reached if everything above succeeded
[ -z "${HEALTHCHECK_URL:-}" ] || wget -q -O /dev/null -T 10 "$HEALTHCHECK_URL" || true
echo "[backup] done"