import httpx
from api_client.base import APIClient

class PersonsClient:
    @staticmethod
    async def get_persons():
        try:
            result = await APIClient.get("/persons/")
            return result.get("persons", []) if result else []
        except httpx.HTTPError:
            return []

    @staticmethod
    async def get_person(person_id: int):
        return await APIClient.get(f"/persons/{person_id}")

    @staticmethod
    async def create_person(data: dict):
        return await APIClient.post("/persons/", data=data)

    @staticmethod
    async def update_person(person_id: int, data: dict):
        return await APIClient.patch(f"/persons/{person_id}", data=data)

    @staticmethod
    async def delete_person(person_id: int):
        return await APIClient.delete(f"/persons/{person_id}")