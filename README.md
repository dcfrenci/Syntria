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
  - [1. Environment Setup](#1-environment-setup)
  - [2. Start Services](#2-start-services)
  - [3. Database Initialization](#3-database-initialization)
- [🌐 Networking \& Access](#-networking--access)
- [🧪 Testing](#-testing)

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

### 1. Environment Setup
Create your environment and install the `requirements.txt`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install scripts/requirements.txt
```
Create your enviroment file by copying the provided example and adding your Tailscale Auth Key:
```bash
cp .env-example .env
```
Edit `.env` and insert your `TS_AUTHKEY` generated from the Tailscale Admin Console


### 2. Start Services
Launch the application stack using Docker Compose:
```bash
docker compose up --build -d
```

### 3. Database Initialization
To set up the database schema and initialize the default Admin user (`admin@email.com` / `asTf82#1`), roles and reminder preferences, run:
```bash
python3 scripts/initialize.py --default
```
> **Note:** If you want to deploy a demonstration environment with pre-filled mock data (patients, catalog items, existing quotes, and sample schedules), run the script without the admin flag: `python3 scripts/initialize.py`

> **Note:** If you want to see all the permissions of the roles or the whole database initialization, check these files: `role_conf.md` and `database_conf.md`

---

## 🌐 Networking & Access
Syntria utilizes **Tailscale** to securely route traffic. Run the following commands from your host machine to configure public and private access:

**1. Enable the Public Frontend (Funnel):**
Map the public HTTPS port 443 to Nginx's public listener on port 80.
```bash
docker exec tailscale_gateway tailscale funnel --bg --https=443 http://nginx:80
```

**2. Enable the Private Backend (Serve):**
Map the private Tailnet HTTPS port 8443 to Nginx's private listener on port 81.
```bash
docker exec tailscale_gateway tailscale serve --bg --https=8443 http://nginx:81
```

---

## 🧪 Testing
To execute automated role permission tests and validate API access controls in an ephemeral environment, run:
```bash
docker compose up --build -d
python3 scripts/initialize.py
python3 scripts/role_testing.py
docker compose down -v
```
>⚠️ **Important**: Because the final command (docker compose down -v) completely destroys the containers and their local volumes, you will need to re-run the commands in the Networking & Access (Tailscale) section when you bring the stack back online for regular use.