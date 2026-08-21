from api_client.base import APIClient

class ServicesClient:
    @staticmethod
    async def get_items(token: str | None = None):
        """Fetches all items/services from FastAPI."""
        result = await APIClient.get("/items/", token=token)
        return result.get("items", []) if result else []

    @staticmethod
    async def create_item(data: dict, token: str | None = None):
        """Creates a new service item matching FastAPI's ItemCreate schema."""
        return await APIClient.post("/items/", data=data, token=token)

    @staticmethod
    async def get_categories(token: str | None = None):
        """Fetches all categories."""
        result = await APIClient.get("/categories/", token=token)
        return result.get("categories", []) if result else []