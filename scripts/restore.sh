#!/usr/bin/env bash
# usage: scripts/restore.sh backups/syntria-YYYYMMDD-HHMMSS.sql.gz[.age] [age-key-file]
set -euo pipefail
cd "$(dirname "$0")/.."
f="${1:?backup file}"; key="${2:-}"
set -a; . ./.env; set +a

read -rp "This REPLACES the contents of '$POSTGRES_DB'. Type 'restore' to continue: " ok
[ "$ok" = "restore" ] || exit 1

docker compose stop api frontend
if [[ "$f" == *.age ]]; then
  [ -n "$key" ] || { echo "encrypted backup: pass the age key file"; exit 1; }
  age -d -i "$key" "$f" | gunzip -c
else
  gunzip -c "$f"
fi | docker compose exec -T db psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose start api frontend