from api_client.base import APIClient

class ServicesClient:
    @staticmethod
    async def get_items():
        """Fetches all items/services."""
        result = await APIClient.get("/items/")
        return result.get("items", []) if result else []
    
    @staticmethod
    async def create_item(data: dict):
        """Creates a new service item."""
        return await APIClient.post("/items/", data=data)
    
    @staticmethod
    async def get_item_with_id(item_id: int):
        """Fetch the item with a specific id."""
        result = await APIClient.get(f"/items/{item_id}")
        return result if result else []
    
    @staticmethod
    async def update_item(item_id: int, data: dict):
        """Update the item with a specific id."""
        return await APIClient.patch(f"/items/{item_id}", data=data)
    
    @staticmethod
    async def delete_item(item_id: int):
        """Delete the item with a specific id."""
        return await APIClient.delete(f"/items/{item_id}")

    @staticmethod
    async def get_categories():
        """Fetches all categories."""
        result = await APIClient.get("/categories/")
        return result.get("categories", []) if result else []
    
    @staticmethod
    async def create_category(data: dict):
        """Creates a new category item."""
        return await APIClient.post("/categories/", data=data)
    
    @staticmethod
    async def get_category_with_id(category_id: int):
        result = await APIClient.get(f"/categories/{category_id}")
        return result if result else []
    
    @staticmethod
    async def update_category(category_id: int, data: dict):
        return await APIClient.patch(f"/categories/{category_id}", data=data)
    
    @staticmethod
    async def detete_category(category_id: int):
        return await APIClient.delete(f"/categories/{category_id}")