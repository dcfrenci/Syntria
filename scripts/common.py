import os
import sys
from urllib.parse import urlparse

# Via Nginx's private tier. The API is no longer published.
BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8081/api/v1")

if urlparse(BASE_URL).hostname not in ("localhost", "127.0.0.1"):
    sys.exit("Refusing to run: seed/reset/test scripts only target a local stack "
             "(they create demo accounts).")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") or sys.exit("Set ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or sys.exit("Set ADMIN_PASSWORD")

# One random password shared by all demo users: nothing sensitive is committed to the repo.
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "")


def require_demo_password() -> str:
    if len(DEMO_PASSWORD) < 12 or len(DEMO_PASSWORD.encode("utf-8")) > 72:
        sys.exit("Set DEMO_PASSWORD (12-72 bytes), e.g. DEMO_PASSWORD=$(openssl rand -hex 16)")
    return DEMO_PASSWORD