from api_client.base import APIClient

class AgendaClient:
    @staticmethod
    async def get_reservations_doctor_week(doctor_id: int, week):
        """Fetches all appointments/reservations."""
        result = await APIClient.get("/reservations/")
        return result.get("reservations", []) if result else []

    @staticmethod
    async def create_reservation(data: dict, token: str | None = None):
        """Creates a new appointment."""
        return await APIClient.post("/reservations/", data=data, token=token)