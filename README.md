<p align="center">
  <picture>
    <img alt="Syntria" src="documentation/images/syntria.svg" width="300">
  </picture>
</p>

<div align="center">
  <em>A comprehensive, full-stack dental clinic management platform designed to streamline daily operations, patient relationships, and clinical administration.</em>
</div>

---

## Table of content

- [Table of content](#table-of-content)
- [📖 Abstract](#-abstract)
- [🏗️ Architecture \& Containerized Services](#️-architecture--containerized-services)
- [🔑 Key Features](#-key-features)
- [🚀 Deployment \& Installation](#-deployment--installation)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Download](#2-download)
  - [3. Environment configuration](#3-environment-configuration)
  - [4. Dependency installation](#4-dependency-installation)
  - [5. Build](#5-build)
  - [6. Database, migrations and first admin](#6-database-migrations-and-first-admin)
  - [7. Run in production mode](#7-run-in-production-mode)
  - [8. Publish with Tailscale (TLS included)](#8-publish-with-tailscale-tls-included)
  - [9. Verify](#9-verify)
  - [10. Backups and restore](#10-backups-and-restore)
  - [11. Updating and rolling back](#11-updating-and-rolling-back)
  - [12. Reverse proxy and SSL alternatives](#12-reverse-proxy-and-ssl-alternatives)

---

## 📖 Abstract
Syntria provides a robust backend API and an intuitive graphical interface for role-based staff access, agenda management, billing, and highly customizable quote document generation.

---

## 🏗️ Architecture & Containerized Services
Syntria is orchestrated via Docker Compose within an isolated custom bridge network (`syntria`). The architecture implements a strict dependency graph utilizing health checks to ensure reliable service initialization and failover.

* **FastAPI (Backend API):**
  * **Implementation:** Built on Python using FastAPI and the Uvicorn ASGI server. It serves as the RESTful backend, handling business logic, async database transactions, and JWT authentication.
  * **Technical Details:** Starts only after the database passes its `pg_isready` health check. Includes a custom `/health` endpoint for stack monitoring.
  * **Advantages:** Delivers high concurrency handling via asynchronous I/O, automatic OpenAPI schema generation, and strict Pydantic data validation to minimize runtime errors.

* **NiceGUI (Reactive UI):**
  * **Implementation:** Built on Python using NiceGUI. It delivers the interactive frontend application directly to staff and clients.
  * **Technical Details:** Bootstraps only after the `api` service is fully healthy, ensuring a seamless data connection upon startup.
  * **Advantages:** Eliminates the need for a separate Javascript/Typescript codebase. It provides real-time UI state synchronization via WebSockets and allows rapid, full-stack feature development using native Python logic.

* **Postgre (Relational Database):**
  * **Implementation:** It stores all system state, including users, patient records, reservations, quotes, and pricing catalogs.
  * **Technical Details:** Uses a persistent local volume (`postgres_data`) to ensure data retention across container restarts. Configured with strict health checks (`interval: 15s`, `retries: 5`).
  * **Advantages:** ACID compliance guarantees strict data integrity for critical clinical and financial records. The Alpine Linux base provides a minimal attack surface and lightweight memory footprint.

* **Pgadmin (Database Administration):**
  * **Implementation:** Deploys `dpage/pgadmin4` for web-based PostgreSQL management.
  * **Technical Details:** Operates safely within the isolated `syntria` network, depending directly on the `db` service.
  * **Advantages:** Provides a secure, graphical interface for complex query execution, schema migrations, and backup management without exposing raw database TCP ports directly to the host machine.

* **Nginx (Reverse Proxy & Ingress):**
  * **Implementation:** Utilizes `nginx:alpine` to manage all incoming HTTP traffic.
  * **Technical Details:** Mounts a read-only configuration file (`nginx.conf`) and depends on the successful boot of the `frontend`, `api`, and `db-web` containers. Validated continuously by internal `wget` spider health checks.
  * **Advantages:** Centralizes HTTP routing, serves static assets efficiently, and enhances security by acting as the sole ingress point, hiding internal container ports behind a single unified gateway.

* **Tailscale (Zero-Trust VPN Gateway):**
  * **Implementation:** Runs the official `tailscale/tailscale` node.
  * **Technical Details:** Configured with elevated network capabilities (`net_admin`, `net_raw`) and a persistent local volume (`tailscale_data`) for identity state management. Authenticates via the injected `TS_AUTHKEY`.
  * **Advantages:** Seamlessly bridges the local Docker network to a private WireGuard-based Tailnet. It allows for the secure, credential-based exposure of internal web interfaces without the need to open vulnerable public firewall ports.

---

## 🔑 Key Features
* **🔐 Role-Based Access Control (RBAC):** Implements stateless JWT authentication with role claims embedded directly in the token payload. Backend routes are secured via FastAPI dependency injection (`Depends(RoleChecker(...))`), enforcing strict HTTP 403 authorization boundaries across 7 hierarchical roles. NiceGUI middleware mirrors this on the frontend to dynamically mount or restrict UI routes.
* **📅 Agenda & Appointments:** Timezone-aware scheduling engine utilizing asynchronous SQLAlchemy queries for precise overlap detection (`start_time < res_end and end_time > res.reservation_date`). The reactive frontend leverages Python-driven DOM updates for calendar rendering, allowing seamless date-range filtering and staff pivoting without full page reloads.
* **👥 Patient CRM:** Normalized relational entity management leveraging SQLAlchemy ORM. Enforces strict Pydantic schema validation for contact data and utilizes foreign key constraints to reliably map patients to their selected reminder infrastructure (SMS, WhatsApp, Telegram).
* **📋 Pricing & Services Catalog:** Centralized master data management for clinical treatments. Ensures absolute financial precision using PostgreSQL `Numeric(10, 2)` column types. Implements `Boolean` database flags (`is_specific`) to programmatically trigger conditional UI logic, such as rendering the interactive tooth-selection matrix.
* **💰 Interactive Quoting System:** Stateful quoting engine that executes multi-table atomic transactions with automatic rollbacks. It handles deep relational payloads, serializing integer arrays for tooth mapping into `JSON` columns, executing server-side subtotal and discount arithmetic, and leveraging `selectinload` for highly optimized eager-loading of the complete quote graph.
* **📄 Drag & Drop Document Presets:** A reactive visual DOM builder calculating absolute X/Y coordinates, spatial boundaries, and viewport scaling in real-time. Template configurations—including font states, bounding boxes, and Base64-encoded image payloads—are serialized and persisted directly into PostgreSQL `JSON` columns for dynamic document generation.
* **🔄 Data Portability:** High-performance ETL pipeline utilizing the `pandas` library for in-memory CSV parsing and generation. It features deep-nested JSON serialization to flatten relational database objects for export, and implements a multi-pass validation layer during imports to prevent primary key conflicts and orphaned foreign key relations before executing atomic bulk commits.

---

## 🚀 Deployment & Installation

Syntria runs as a Docker Compose stack: `db` (PostgreSQL 16), `api` (FastAPI), `frontend` (NiceGUI), `nginx` (two-tier reverse proxy), `backup` (encrypted pg_dump loop) and `tailscale` (HTTPS ingress). Nothing needs to be installed on the host except Docker and a few CLI tools.

### 1. Prerequisites

| Requirement           | Minimum                  | Notes                                                                                                                                                                   |
| --------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Linux host            | Ubuntu 22.04 / Debian 12 | amd64 or arm64                                                                                                                                                          |
| CPU / RAM / disk      | 2 vCPU / 2 GB / 10 GB    | Container limits in the compose file sum to about 1.7 GB (+384 MB if pgAdmin is enabled)                                                                                |
| Docker Engine         | 24.0                     |                                                                                                                                                                         |
| Docker Compose plugin | 2.20                     | Needs `--wait`, `depends_on: service_healthy` and `profiles`                                                                                                            |
| git, openssl          | any recent               | `gen-env.sh` uses `openssl`                                                                                                                                             |
| `age`                 | 1.0                      | On the **host**, for `restore.sh` and key handling (`apt install age`)                                                                                                  |
| Python 3 + `venv`     | 3.9                      | Host-side only, for `scripts/*.py` (tests/seed). The containers use Python **3.12** (the code relies on 3.12 f-string syntax, so never set `PYTHON_VERSION` below 3.12) |
| Tailscale account     | –                        | MagicDNS and HTTPS certificates enabled, Funnel allowed in the ACL (`nodeAttrs` → `funnel`), and a reusable or one-off **auth key**                                     |

### 2. Download

```bash
git clone https://github.com/dcfrenci/Syntria.git
cd Syntria
git checkout <release-tag>      # optional: deploy a tagged release instead of master
```

### 3. Environment configuration

```bash
./scripts/gen-env.sh
```

This creates `.env` from `.env-example.conf` and generates random values for the database password, pgAdmin password, `SECRET_KEY` and `NICEGUI_STORAGE_SECRET`. It also creates `backups/` and `backup/rclone/` owned by you. It refuses to overwrite an existing `.env`.

> ⚠️ Never `cp .env-example.conf .env` for production: the example ships `admin/admin` database credentials.

Then set the remaining values by hand:

```bash
chmod 600 .env
sed -i 's|^ADMIN_EMAIL=.*|ADMIN_EMAIL=owner@yourclinic.it|' .env
sed -i 's|^COMPOSE_PROFILES=.*|COMPOSE_PROFILES=tailscale|' .env     # production: tailscale, NOT tools
sed -i 's|^# COMPOSE_FILE=|COMPOSE_FILE=|' .env                       # never load docker-compose.override.yaml (dev bind-mounts + --reload)
nano .env                                                             # TS_AUTHKEY, AGE_RECIPIENT, RCLONE_REMOTE, HEALTHCHECK_URL
```

`.env` is also sourced by `restore.sh` and `bootstrap.sh`, so quote values containing spaces, `#` or `$`.

| Variable                                                                     | Required   | Purpose                                                                                                                                                  | Production value                    |
| ---------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- |
| `PYTHON_VERSION`                                                             | yes        | Base image tag (build arg)                                                                                                                               | `3.12-slim`                         |
| `POSTGRES_IMAGE`                                                             | yes        | DB image; the `backup` image is built from the same one, so `pg_dump` matches the server major version                                                   | `postgres:16-alpine`                |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`                        | yes        | DB credentials (URL-encoded automatically, so special characters are safe)                                                                               | generated by `gen-env.sh`           |
| `POSTGRES_HOST` / `POSTGRES_PORT`                                            | yes        | Must be the compose service name and port                                                                                                                | `db` / `5432`                       |
| `ADMIN_EMAIL`                                                                | yes        | Login of the system admin. The API also **hides** this person from non-admin users, so choose it once                                                    | `owner@yourclinic.it`               |
| `SECRET_KEY`                                                                 | yes        | JWT signing key. The API refuses to start if it is shorter than 32 chars or contains `change_me`/`supersecret`/`changeme`. Rotating it logs everyone out | generated (≈80 chars)               |
| `FASTAPI_PORT` / `NICEGUI_PORT`                                              | yes        | Internal ports. **Do not change**: `nginx.conf` hardcodes `api:8000` and `frontend:8080`                                                                 | `8000` / `8080`                     |
| `NICEGUI_STORAGE_SECRET`                                                     | yes        | Signs the UI session cookie (empty = insecure). Rotating it logs everyone out                                                                            | generated                           |
| `API_BASE_URL`                                                               | yes        | How the frontend reaches the API (server-to-server, inside Docker)                                                                                       | `http://api:${FASTAPI_PORT}/api/v1` |
| `NGINX_IMAGE`, `TAILSCALE_IMAGE`, `PGADMIN_IMAGE`                            | yes        | Image tags. Pin exact versions in production instead of `latest`                                                                                         | e.g. `nginx:1.27-alpine`            |
| `TAILSCALE_CONTAINER_NAME`                                                   | yes        | Used by the `docker exec` commands below                                                                                                                 | `tailscale_gateway`                 |
| `TAILSCALE_HOSTNAME`                                                         | yes        | Name of the node on your tailnet (becomes `<name>.<tailnet>.ts.net`)                                                                                     | `syntria`                           |
| `TS_AUTHKEY`                                                                 | prod       | Tailscale auth key, used on first start (state then persists in the `tailscale_data` volume)                                                             | `tskey-auth-…`                      |
| `COMPOSE_PROFILES`                                                           | yes        | `tailscale` = production ingress. `tools` = pgAdmin (dev only)                                                                                           | `tailscale`                         |
| `COMPOSE_FILE`                                                               | prod       | Uncomment to disable the dev override file                                                                                                               | `docker-compose.yaml`               |
| `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD` / `PGADMIN_LISTEN_PORT` | tools only | pgAdmin login. Keep the listen port at `5050` (hardcoded in `nginx.conf`)                                                                                | generated / `5050`                  |
| `BACKUP_UID` / `BACKUP_GID`                                                  | yes        | Owner of dump files (set by `gen-env.sh`)                                                                                                                | your `id -u` / `id -g`              |
| `BACKUP_KEEP_DAYS` / `BACKUP_INTERVAL_HOURS`                                 | no         | Retention and frequency                                                                                                                                  | `14` / `24`                         |
| `AGE_RECIPIENT`                                                              | prod       | `age1…` public key. Dumps are encrypted with it; required when `RCLONE_REMOTE` is set                                                                    | see §10                             |
| `RCLONE_REMOTE`                                                              | no         | Off-site target, e.g. `gdrive:syntria-backups` or `b2:bucket/syntria`                                                                                    | optional but recommended            |
| `HEALTHCHECK_URL`                                                            | no         | healthchecks.io ping URL, hit only after a successful backup                                                                                             | optional but recommended            |

`PROJECT_NAME`, `*_CONTAINER_NAME` (except Tailscale) and `PGADMIN_PORT` are currently not referenced by `docker-compose.yaml`.

### 4. Dependency installation

Nothing to install on the host for the app itself. The images install **only** the pinned production lockfiles (`api/requirements.lock`, `frontend/requirements.lock`) with `pip install -r requirements.lock`.

To change dependencies, edit `requirements.txt`, regenerate the lockfile in a clean venv (`pip install -r requirements.txt && pip freeze > requirements.lock`), commit both, and rebuild.

Host-side tooling (only needed for the test suite / demo data):

```bash
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
```

### 5. Build

```bash
docker compose config -q                               # validates .env interpolation
docker compose config | grep -c -- '--reload'          # must print 0 (dev override NOT loaded)
docker compose build --pull
```

### 6. Database, migrations and first admin

Migrations are automatic: the `api` container runs `alembic upgrade head` before starting uvicorn.

**Fresh install**, after the stack is up (§7):

```bash
docker compose exec api python -m app.cli bootstrap
```

This seeds the 7 roles and the reminder preferences, then creates the admin `ADMIN_EMAIL`. It prompts for the password (≥ 12 chars, ≤ 72 bytes). It is idempotent. If the admin ever loses access: `docker compose exec api python -m app.cli set-password`.

**Existing database created before Alembic was introduced** (tables already exist). Stamp the baseline once, **before** starting `api`, or it will crash-loop on `CREATE TABLE`:

```bash
docker compose up -d db
docker compose run --rm --no-deps api alembic stamp head
```

Rotate the old `admin/admin` DB credentials as described in `backup/backup_conf.md` ("Existing deployment").

**Never run `scripts/initialize.py --pre-filled` in production.** It creates accounts with publicly documented passwords (it is also guarded to run only against localhost).

New migrations are generated in development, where the override file mounts `api/migrations`: `docker compose exec api alembic revision --autogenerate -m "msg"`. Commit the file and redeploy.

### 7. Run in production mode

Option A, one command (runs the permission test-suite on an isolated throw-away stack first, then starts the real one and asks for the admin password):

```bash
./scripts/bootstrap.sh              # strict: real stack is not started if tests fail
```

Option B, manual:

```bash
docker compose up -d --build --wait --wait-timeout 240
docker compose ps                   # every service: healthy
docker compose exec api python -m app.cli bootstrap
```

All services use `restart: unless-stopped`, so they come back after a reboot (make sure `systemctl enable docker`).

### 8. Publish with Tailscale (TLS included)

Nginx publishes no host ports in production. Traffic enters only through the Tailscale container:

```bash
# Public tier: the web app only (/api and /pgadmin return 403 here)
docker exec tailscale_gateway tailscale funnel --bg --https=443 http://nginx:80
# Private tier: app + API + pgAdmin, reachable only from your tailnet
docker exec tailscale_gateway tailscale serve  --bg --https=8443 http://nginx:81
docker exec tailscale_gateway tailscale funnel status
```

The container's Funnel/Serve config is stored in the `tailscale_data` volume, so it survives restarts but **not** `docker compose down -v` (re-run the commands).

### 9. Verify

```bash
docker compose ps
curl -s -o /dev/null -w '%{http_code}\n' https://<node>.<tailnet>.ts.net/api/v1/users/        # 403 (public tier blocks /api)
curl -s -o /dev/null -w '%{http_code}\n' https://<node>.<tailnet>.ts.net:8443/api/v1/users/   # 401 from inside the tailnet
docker compose exec backup /usr/local/bin/backup.sh && ls -la backups/                         # a fresh syntria-*.sql.gz[.age]
```

From a machine **outside** the tailnet, `nmap -p 5432,5050,8000,8080,8081 <host-ip>` must show all ports closed. Then log in, open a table page, and upload a preset image of about 1 MB to confirm WebSocket and body-size settings through nginx.

### 10. Backups and restore

```bash
docker compose build backup
docker compose run --rm --no-deps -T --entrypoint age-keygen backup > backup-key.txt
grep -i 'public key' backup-key.txt      # put the age1… value in AGE_RECIPIENT, then move backup-key.txt OFF this server
docker compose up -d backup
```

Off-site upload (Google Drive / B2 / R2) is described in `backup/backup_conf.md`. Uploads are refused unless the dump is age-encrypted. **If you lose the age key, the encrypted backups are unrecoverable.**

Restore (stops `api` and `frontend`, replaces the DB contents):

```bash
scripts/restore.sh backups/syntria-YYYYMMDD-HHMMSS.sql.gz.age backup-key.txt
```

Do a restore drill into a scratch Postgres container before relying on the backups (commands in `backup/backup_conf.md`).

### 11. Updating and rolling back

```bash
docker compose exec backup /usr/local/bin/backup.sh     # always back up first
git pull --ff-only
docker compose up -d --build --wait                     # migrations run automatically on api start
```

Rollback: `git checkout <previous-tag> && docker compose up -d --build --wait`. If the release included a schema migration, also restore the pre-update dump with `restore.sh`.

### 12. Reverse proxy and SSL alternatives

**Default (recommended):** Tailscale Funnel/Serve terminates TLS with auto-renewed certificates, so no certbot is needed.

**Without Tailscale** (classic VPS): publish the internal nginx on loopback only and terminate TLS on the host.

```yaml
# docker-compose.ports.yaml (use: COMPOSE_FILE=docker-compose.yaml:docker-compose.ports.yaml)
services:
  nginx:
    ports: ["127.0.0.1:8080:80"]       # public tier only; do NOT publish port 81
```

```nginx
# /etc/nginx/sites-available/syntria  (then: certbot --nginx -d clinic.example.com)
server {
    listen 443 ssl http2;
    server_name clinic.example.com;
    # ssl_certificate / ssl_certificate_key managed by certbot

    client_max_body_size 10m;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;          # NiceGUI uses WebSockets
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 3600s;
    }
}
server { listen 80; server_name clinic.example.com; return 301 https://$host$request_uri; }
```

Keep the API and pgAdmin off the internet: they are only exposed by the private tier (port 81), never by the snippet above.

