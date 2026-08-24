from api_client.base import APIClient

class ServicesClient:
    @staticmethod
    async def get_items():
        """Fetches all items/services from FastAPI."""
        result = await APIClient.get("/items/")
        return result.get("items", []) if result else []

    @staticmethod
    async def create_item(data: dict):
        """Creates a new service item matching FastAPI's ItemCreate schema."""
        return await APIClient.post("/items/", data=data)

    @staticmethod
    async def get_categories():
        """Fetches all categories."""
        result = await APIClient.get("/categories/")
        return result.get("categories", []) if result else []