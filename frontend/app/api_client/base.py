import logging
import os

import httpx
from nicegui import app

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
log = logging.getLogger("syntria.api_client")

_client: httpx.AsyncClient | None = None


def _http() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=3.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _client


async def _close_client():
    if _client is not None and not _client.is_closed:
        await _client.aclose()


app.on_shutdown(_close_client)


def _headers() -> dict:
    token = app.storage.user["token"] if app.storage.user.get("authenticated", False) else None
    return {"Authorization": f"Bearer {token}"} if token else {}


class APIClient:
    """Centralized HTTP client for communicating with the FastAPI backend."""

    @staticmethod
    async def _request(method: str, endpoint: str, *, params=None, json=None):
        try:
            response = await _http().request(
                method, f"{BASE_URL}{endpoint}", headers=_headers(), params=params, json=json
            )
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError:
            raise  # propagate status errors (403, 409...) to the UI
        except httpx.HTTPError as e:
            log.error("%s %s failed: %s", method, endpoint, e)
            return None

    @staticmethod
    async def get(endpoint: str, params: dict | None = None) -> dict | list | None:
        res = await APIClient._request("GET", endpoint, params=params)
        return res.json() if res is not None else None

    @staticmethod
    async def post(endpoint: str, data: dict) -> dict | None:
        res = await APIClient._request("POST", endpoint, json=data)
        return res.json() if res is not None else None

    @staticmethod
    async def patch(endpoint: str, data: dict) -> dict | None:
        res = await APIClient._request("PATCH", endpoint, json=data)
        return res.json() if res is not None else None

    @staticmethod
    async def delete(endpoint: str) -> bool:
        res = await APIClient._request("DELETE", endpoint)
        return res is not None