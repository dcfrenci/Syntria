import httpx
from api_client.base import APIClient

class UsersClient:
    @staticmethod
    async def get_users():
        try:
            res = await APIClient.get("/users/")
            return res.get("users", []) if res else []
        except httpx.HTTPError:
            return []

    @staticmethod
    async def get_user_me():
        res = await APIClient.get(f"/users/me")
        return res.get("users", []) if res else []

    @staticmethod
    async def get_user(user_id: int):
        return await APIClient.get(f"/users/{user_id}")

    @staticmethod
    async def create_user(data: dict):
        return await APIClient.post("/users/", data=data)

    @staticmethod
    async def update_user(user_id: int, data: dict):
        return await APIClient.patch(f"/users/{user_id}", data=data)

    @staticmethod
    async def delete_user(user_id: int):
        return await APIClient.delete(f"/users/{user_id}")