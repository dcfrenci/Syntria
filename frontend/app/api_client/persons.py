from api_client.base import APIClient

class PersonsClient:
    @staticmethod
    async def get_persons():
        """Fetches all quotes."""
        result = await APIClient.get("/persons/")
        return result.get("persons", []) if result else []