import os
import sys
from urllib.parse import urlparse

# Via Nginx's private tier. The API is no longer published.
BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8081/api/v1")

if urlparse(BASE_URL).hostname not in ("localhost", "127.0.0.1"):
    sys.exit("Refusing to run: seed/reset/test scripts only target a local stack "
             "(they use public demo passwords).")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") or sys.exit("Set ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or sys.exit("Set ADMIN_PASSWORD")