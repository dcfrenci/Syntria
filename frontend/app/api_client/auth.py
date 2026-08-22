import httpx

import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv('API_BASE_URL')
    
async def authenticate(username: str, password: str):
    # FastAPI OAuth2 typically expects form data:
    data = {"username": username, "password": password}
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/auth/token", data=data)
        if response.status_code == 200:
            return response.json()  # Returns {"access_token": "...", "token_type": "bearer"}
        return None