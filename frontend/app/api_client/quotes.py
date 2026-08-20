from app.api_client.base import APIClient

class QuotesClient:
    @staticmethod
    async def get_quotes(token: str | None = None):
        """Fetches all quotes."""
        result = await APIClient.get("/quotes/", token=token)
        return result.get("quotes", []) if result else []

    @staticmethod
    async def create_quote(data: dict, token: str | None = None):
        """Creates a customized quotation."""
        return await APIClient.post("/quotes/", data=data, token=token)