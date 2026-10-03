import httpx
from api_client.base import APIClient

class ServicesClient:
    @staticmethod
    async def get_items(is_active: bool | None = None):
        """Fetches all items/services with pagination and optional filtering."""
        try:
            all_items = []
            skip = 0
            limit = 100

            while True:
                params = {"skip": skip, "limit": limit}
                if is_active is not None:
                    params["is_active"] = is_active

                result = await APIClient.get("/items/", params=params)
                
                if not result:
                    break
                    
                batch = result.get("items", [])
                if not batch:
                    break
                    
                all_items.extend(batch)
                
                total = result.get("total", 0)
                skip += limit
                
                if skip >= total:
                    break
                    
            return all_items
        except httpx.HTTPError:
            return []
    
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
    async def get_categories(is_active: bool | None = None):
        """Fetches all categories with pagination and optional filtering."""
        try:
            all_categories = []
            skip = 0
            limit = 100

            while True:
                params = {"skip": skip, "limit": limit}
                if is_active is not None:
                    params["is_active"] = is_active

                result = await APIClient.get("/categories/", params=params)
                
                if not result:
                    break
                    
                batch = result.get("categories", [])
                if not batch:
                    break
                    
                all_categories.extend(batch)
                
                total = result.get("total", 0)
                skip += limit
                
                if skip >= total:
                    break
                    
            return all_categories
        except httpx.HTTPError:
            return []
    
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
    async def delete_category(category_id: int):
        return await APIClient.delete(f"/categories/{category_id}")