import httpx

from api_client.base import APIClient


class UsersClient:
    @staticmethod
    async def get_users(role: str | None = None, is_active: bool | None = None):
        try:
            all_users, skip, limit = [], 0, 100
            while True:
                params = {"skip": skip, "limit": limit}
                if role:
                    params["role"] = role
                if is_active is not None:
                    params["is_active"] = is_active
                res = await APIClient.get("/users/", params=params)
                if not res:
                    break
                batch = res.get("users", [])
                if not batch:
                    break
                all_users.extend(batch)
                skip += limit
                if skip >= res.get("total", 0):
                    break
            return all_users
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                return []
            raise

    @staticmethod
    async def get_user_me():
        return await APIClient.get(f"/users/me")

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
