from api_client.base import APIClient

class QuotesClient:
    @staticmethod
    async def get_quotes():
        """Fetches all quotes."""
        result = await APIClient.get("/quotes/")
        return result.get("quotes", []) if result else []
    
    @staticmethod
    async def get_quote_with_id(id: int):
        """Fetches the quote with a specific id."""
        result = await APIClient.get(f"/quotes/{id}")
        return result if result else []

    @staticmethod
    async def create_quote(data: dict):
        """Creates a customized quotation."""
        return await APIClient.post("/quotes/", data=data)
    
    @staticmethod
    async def update_quote(quote_id: int, data: dict):
        """Update the quote with a specific id."""
        return await APIClient.patch(f"/quotes/{quote_id}", data=data)
    
    @staticmethod
    async def delete_quote(quote_id: int):
        """Delete the quote with a specific id."""
        return await APIClient.delete(f"/quotes/{quote_id}")