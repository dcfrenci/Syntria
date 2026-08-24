from api_client.base import APIClient

class QuotesClient:
    @staticmethod
    async def get_quotes():
        """Fetches all quotes."""
        result = await APIClient.get("/quotes/")
        return result.get("quotes", []) if result else []

    @staticmethod
    async def create_quote(data: dict):
        """Creates a customized quotation."""
        return await APIClient.post("/quotes/", data=data)