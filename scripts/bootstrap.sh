#!/usr/bin/env bash
# usage: scripts/bootstrap.sh [--advisory | --skip-tests]
#   (default)     tests must pass, otherwise the real stack is NOT started
#   --advisory    run tests, print failures, start the real stack anyway
#   --skip-tests  do not run tests
set -euo pipefail
cd "$(dirname "$0")/.."

MODE=strict
case "${1:-}" in
  "") ;;
  --advisory) MODE=advisory ;;
  --skip-tests) MODE=skip ;;
  *) echo "usage: $0 [--advisory|--skip-tests]" >&2; exit 2 ;;
esac

# ---------- 1. .env ----------
[ -e .env ] || ./scripts/gen-env.sh
set -a; . ./.env; set +a
if [ -z "${ADMIN_EMAIL:-}" ] || [ "$ADMIN_EMAIL" = "admin@your-clinic.it" ]; then
  echo "Edit ADMIN_EMAIL in .env first, then re-run." >&2
  exit 1
fi

# ---------- 2. preflight ----------
if ! ls api/migrations/versions/*.py >/dev/null 2>&1; then
  echo "No migration in api/migrations/versions/. Generate the baseline first (step 5)." >&2
  exit 1
fi
for f in api/requirements.lock frontend/requirements.lock; do
  [ -f "$f" ] || { echo "Missing $f. Generate the lockfiles first." >&2; exit 1; }
done

rand() { openssl rand -base64 64 | tr -d '/+=\n' | cut -c1-40; }

# ---------- 3. test phase (isolated stack, throwaway secrets) ----------
TEST_STARTED=0
TEST_EMAIL="admin@syntria-test.dev"
TEST_PW="$(rand)"
TEST_DEMO_PW="$(rand)"
TEST_DBPW="$(rand)"
TEST_KEY="$(rand)$(rand)"

# Explicit -f files: the dev override is NOT loaded. Different project name = separate volumes.
tc() {
  env COMPOSE_PROFILES= POSTGRES_PASSWORD="$TEST_DBPW" SECRET_KEY="$TEST_KEY" ADMIN_EMAIL="$TEST_EMAIL" \
    docker compose -p syntria-test -f docker-compose.yaml -f docker-compose.test.yaml "$@"
}

cleanup_test() {
  if [ "$TEST_STARTED" = 1 ]; then
    echo "Removing test stack..."
    tc down -v --remove-orphans >/dev/null 2>&1 || true
    TEST_STARTED=0
  fi
}

python_with_requests() {
  if [ -x .venv/bin/python ] && .venv/bin/python -c "import requests" 2>/dev/null; then
    echo .venv/bin/python
  elif python3 -c "import requests" 2>/dev/null; then
    echo python3
  else
    python3 -m venv .venv >&2 && .venv/bin/pip install -q -r scripts/requirements.txt >&2 \
      && echo .venv/bin/python
  fi
}

run_suite() {
  local py; py="$(python_with_requests)" || return 1
    local suite_env=(ADMIN_EMAIL="$TEST_EMAIL" ADMIN_PASSWORD="$TEST_PW" DEMO_PASSWORD="$TEST_DEMO_PW"
                   API_BASE_URL="http://127.0.0.1:18081/api/v1")

  tc up -d --build --wait --wait-timeout 240 nginx || { tc logs --tail=40 api; return 1; }
  tc exec -T -e ADMIN_PASSWORD="$TEST_PW" api python -m app.cli bootstrap || return 1
  env "${suite_env[@]}" "$py" scripts/initialize.py --pre-filled || return 1
  env "${suite_env[@]}" "$py" scripts/role_testing.py || return 1
}

if [ "$MODE" != skip ]; then
  echo "== Test phase (project syntria-test, ports 18080/18081) =="
  TEST_STARTED=1
  trap cleanup_test EXIT
  if run_suite; then
    echo "== Tests passed =="
  else
    cleanup_test
    if [ "$MODE" = strict ]; then
      echo "Tests FAILED. The real stack was not started. Use --advisory to start anyway." >&2
      exit 1
    fi
    echo "Tests FAILED (advisory mode): continuing." >&2
  fi
  cleanup_test
  trap - EXIT
fi

# ---------- 4. real stack ----------
echo "== Starting the real stack =="
docker compose up -d --build --wait --wait-timeout 240 api   # waits for db + api healthy
docker compose up -d                                         # everything else (no wait: backup is slow to report healthy)

# ---------- 5. admin (prompts for the password; idempotent) ----------
docker compose exec api python -m app.cli bootstrap

echo
if [[ "${COMPOSE_PROFILES:-}" == *tailscale* ]]; then
  echo "Done. Production profile active: configure Funnel/Serve as in the README."
else
  echo "Done. App: http://localhost:8080   API docs: http://localhost:8081/api/docs"
fi