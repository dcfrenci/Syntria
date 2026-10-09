from api_client.base import APIClient


class AgendaClient:
    @staticmethod
    async def get_reservations_week(
        start_date: str, doctor_id: int | None = None, end_date: str | None = None
    ):
        """Fetches reservations. If doctor_id is None, it defaults to the logged-in user. If end_date is None, returns the whole week."""
        query_params = {"start_date": start_date}

        # Add optional parameters to the query
        if end_date:
            query_params["end_date"] = end_date
        if doctor_id is not None:
            query_params["user_id"] = doctor_id

        result = await APIClient.get("/reservations/", params=query_params)
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
