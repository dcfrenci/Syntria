import httpx
from api_client.base import APIClient

class RolesClient:
    @staticmethod
    async def get_roles() -> list[dict]:
        try:
            res = await APIClient.get("/roles/")
            return res if res is not None else []
        except httpx.HTTPError:
            return []

    @staticmethod
    async def create_role(data: dict):
        return await APIClient.post("/roles/", data=data)