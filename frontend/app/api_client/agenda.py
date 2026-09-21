from api_client.base import APIClient

class AgendaClient:
    @staticmethod
    async def get_reservations_doctor_week(doctor_id: int, start_date: str, end_date: str | None = None):
        """Fetches reservations for a specific doctor.If end_date is None, the backend automatically returns the whole week of start_date."""
        query_params = {
            "start_date": start_date
        }
        if end_date:
            query_params["end_date"] = end_date
        result = await APIClient.get(f"/users/{doctor_id}/reservations", params=query_params)
        return result.get("reservations", []) if result else []

    @staticmethod
    async def get_reservation_with_id(reservation_id: int):
        """Get the reservation with a specific id."""
        return await APIClient.get(f"/reservations/{reservation_id}")
    
    @staticmethod
    async def create_reservation(data: dict):
        """Creates a new appointment."""
        return await APIClient.post("/reservations/", data=data)
    
    @staticmethod
    async def update_reservation(reservation_id: int, data: dict):
        """Update an appointment with a specific id."""
        return await APIClient.patch(f"/reservations/{reservation_id}", data=data)
    
    @staticmethod
    async def delete_reservation(reservation_id: int):
        """Delete an appointment with a specific id"""
        return await APIClient.delete(f"/reservations/{reservation_id}")