# Free off-site options
| Option                                         | Notes                                                                                                                                                                                                                   |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Local only (default)                           | Dumps land in `./backups`. Copy that folder to a USB disk or NAS regularly, e.g. `rsync -a backups/ user@nas:/srv/syntria/`. A backup on the same disk as the database does not protect against disk failure or ransomware. |
| Google Drive (15 GB free)                      | Via `rclone`, set up below.                                                                                                                                                                                               |
| Backblaze B2 / Cloudflare R2 (10 GB free each) | Better fit for unattended jobs: plain API keys, no OAuth token to expire. Configure a remote with rclone config the same way, then set `RCLONE_REMOTE=b2:bucket/syntria`.                                                 |

Because dumps are encrypted with `age` before leaving the host, the storage provider only ever holds ciphertext. Check with your DPO whether that is enough for your GDPR position.

Generate the encryption key. Keep the private key off the server, in a password manager plus a printed copy:

```bash
mkdir -p backups backup/rclone
docker compose build backup
docker compose run --rm --no-deps -T --entrypoint age-keygen backup > backup-key.txt
grep 'public key' backup-key.txt     # put the age1... value in AGE_RECIPIENT
# then move backup-key.txt off this machine
```

If you lose this key, the encrypted backups are unrecoverable.

Connect Google Drive (one-time):

```bash
docker compose run --rm -it --no-deps --entrypoint rclone backup config
```
1. Choose n (new remote), name it gdrive, and pick storage type drive.
2. Leave the client ID blank, or use your own to avoid rclone’s shared rate limit.
3. Choose scope 3 (drive.file), so rclone can only touch files it created.
4. When asked “Use web browser to automatically authenticate?”, answer n. Run the rclone authorize "drive" "..." command it prints on any machine with a browser, and paste the token back.
5. The config is saved to `./backup/rclone/rclone.conf`.

Then set `RCLONE_REMOTE=gdrive:syntria-backups` and `AGE_RECIPIENT=age1...` in `.env` and run `docker compose up -d backup`.

If you use your own OAuth client, publish it to “In production” in Google Cloud. Apps left in “Testing” have refresh tokens that expire after 7 days, and backups will silently stop uploading.

The host needs `age` installed (`apt install age` or `brew install age`) for encrypted dumps. Do the restore drill now, against a scratch database that never touches your live one:
```bash
latest=$(ls -t backups/syntria-* | head -1)
docker run -d --name pgtest -e POSTGRES_PASSWORD=x postgres:16-alpine && sleep 5
( [[ $latest == *.age ]] && age -d -i backup-key.txt "$latest" || cat "$latest" ) | gunzip -c \
  | docker exec -i pgtest psql -q -U postgres
docker exec pgtest psql -U postgres -c "select count(*) from persons;"
docker rm -f pgtest
```

# Runbooks
Fresh local install
```bash
./scripts/gen-env.sh && nano .env                     # set ADMIN_EMAIL
docker compose up -d --build                          # override file is auto-loaded
docker compose exec api python -m app.cli bootstrap   # prompts for the admin password
# App: http://localhost:8080   API/pgAdmin: http://localhost:8081
# Optional demo data:
ADMIN_EMAIL=... ADMIN_PASSWORD=... python3 scripts/initialize.py --pre-filled
```
Fresh production install
```bash
./scripts/gen-env.sh
# edit .env: ADMIN_EMAIL, TS_AUTHKEY, COMPOSE_PROFILES=tailscale, AGE_RECIPIENT, RCLONE_REMOTE
docker compose -f docker-compose.yaml up -d --build
docker compose exec api python -m app.cli bootstrap
# then the existing README "Networking & Access" funnel/serve commands
```
Do not run `initialize.py --pre-filled` in production. It seeds accounts with publicly known passwords, and the new loopback guard will refuse anyway.

Existing deployment (live data, old admin/admin DB credentials)
Postgres reads `POSTGRES_PASSWORD` only when a volume is first created, so changing .env alone does nothing:
```bash
# 1. back up first (the new backup service, or a manual pg_dump)
# 2. keep your existing POSTGRES_USER in .env, and rotate the password inside the DB:
docker compose exec db psql -U admin -d db -c "ALTER USER admin WITH PASSWORD '<new random>'"
# 3. put the same value in .env, set a new SECRET_KEY (this logs everyone out), and a new PGADMIN_DEFAULT_PASSWORD
# 4. set ADMIN_EMAIL=admin@email.com (your current admin), then rotate its password:
docker compose exec api python -m app.cli set-password
docker compose up -d --build
```
Recreating the containers drops the old published ports.

# Verification checklist
```bash
# Local: only Nginx on loopback
ss -tlnp | grep -E ':(5432|5050|8000|8080|8081)\b'      # expect only 127.0.0.1:8080 and :8081
# Production: expect NONE of them; from another machine:
nmap -p 5432,5050,8000,8080,8081 <host-ip>              # all closed/filtered

curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8080/api/v1/users/           # 403 (public tier blocks /api)
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8081/api/v1/users/           # 401 (needs a token)
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8081/api/v1/users/admin   # 405 (endpoint gone)

docker compose exec backup /usr/local/bin/backup.sh && ls -la backups/                 # a fresh syntria-*.sql.gz[.age]
docker compose ps                                                                      # backup: healthy
```
Also log in through `http://localhost:8080`, open a page with live tables, and upload a preset image over 1 MB. That confirms the WebSocket and body-size settings work through Nginx. Run the restore drill above before you call this done.