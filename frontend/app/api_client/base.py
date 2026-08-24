import httpx
from nicegui import app

# In Docker, your FastAPI backend container is accessible via http://api:8000
BASE_URL = "http://api:8000/api/v1"

class APIClient:
    """Centralized HTTP client for communicating with the FastAPI backend."""
    
    @staticmethod
    async def get(endpoint: str) -> dict | list | None:
        token = app.storage.user['token'] if app.storage.user.get('authenticated', False) else None
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}", headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"GET request failed for {endpoint}: {e}")
                return None

    @staticmethod
    async def post(endpoint: str, data: dict) -> dict | None:
        token = app.storage.user['token'] if app.storage.user.get('authenticated', False) else None
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"POST request failed for {endpoint}: {e}")
                return None

    @staticmethod
    async def patch(endpoint: str, data: dict) -> dict | None:
        token = app.storage.user['token'] if app.storage.user.get('authenticated', False) else None
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(f"{BASE_URL}{endpoint}", json=data, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"PATCH request failed for {endpoint}: {e}")
                return None

    @staticmethod
    async def delete(endpoint: str) -> bool:
        token = app.storage.user['token'] if app.storage.user.get('authenticated', False) else None
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(f"{BASE_URL}{endpoint}", headers=headers)
                response.raise_for_status()
                return True
            except httpx.HTTPError as e:
                print(f"DELETE request failed for {endpoint}: {e}")
                return False