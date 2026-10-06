import httpx

import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    
async def authenticate(username: str, password: str):
    data = {"username": username, "password": password}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/auth/token", data=data)
        if response.status_code == 200:
            return response.json()
        return None