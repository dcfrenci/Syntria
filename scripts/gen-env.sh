#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[ -e .env ] && { echo ".env already exists, refusing to overwrite"; exit 1; }

umask 077
rand() { openssl rand -base64 64 | tr -d '/+=\n' | cut -c1-40; }   # alphanumeric: safe in URLs/sed

sed -e "s|^POSTGRES_USER=.*|POSTGRES_USER=syntria|" \
    -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(rand)|" \
    -e "s|^PGADMIN_DEFAULT_PASSWORD=.*|PGADMIN_DEFAULT_PASSWORD=$(rand)|" \
    -e "s|^SECRET_KEY=.*|SECRET_KEY=$(rand)$(rand)|" \
    -e "s|^BACKUP_UID=.*|BACKUP_UID=$(id -u)|" \
    -e "s|^BACKUP_GID=.*|BACKUP_GID=$(id -g)|" \
    .env-example.conf > .env

mkdir -p backups backup/rclone          # must be owned by you, not created by Docker as root
echo ".env generated. Now edit ADMIN_EMAIL (and TS_AUTHKEY for production)."