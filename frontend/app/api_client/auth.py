import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


async def authenticate(username: str, password: str, client_ip: str | None = None):
    data = {"username": username, "password": password}
    headers = {"X-Real-IP": client_ip} if client_ip and client_ip != "unknown" else {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/auth/token", data=data, headers=headers)
        except httpx.HTTPError:
            return {"error": "unavailable"}
    if response.status_code == 200:
        return response.json()
    if response.status_code == 429:
        return {"error": "rate_limited"}
    return None