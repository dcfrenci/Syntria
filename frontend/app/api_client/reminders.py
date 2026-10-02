import httpx
from api_client.base import APIClient

class RemindersClient:
    @staticmethod
    async def get_preferences() -> list[dict]:
        try:
            res = await APIClient.get("/reminders/")
            return res if res is not None else []
        except httpx.HTTPError:
            return []
        
    @staticmethod
    async def create_preference(data: dict):
        return await APIClient.post("/reminders/", data=data)