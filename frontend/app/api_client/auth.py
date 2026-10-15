import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


async def authenticate(username: str, password: str):
    """Returns the token dict on success, None on bad credentials,
    or {"error": "rate_limited" | "unavailable"}."""
    data = {"username": username, "password": password}
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(f"{BASE_URL}/auth/token", data=data)
        except httpx.HTTPError:
            return {"error": "unavailable"}
    if response.status_code == 200:
        return response.json()
    if response.status_code == 429:
        return {"error": "rate_limited"}
    return None