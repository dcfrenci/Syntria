import os
import httpx
from nicegui import app, ui
from api_client.base import APIClient

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def _detail(res: httpx.Response) -> str:
    try:
        d = res.json().get("detail")
    except Exception:
        d = None
    return str(d or res.text or res.status_code)[:300]


class DataClient(APIClient):
    """Manages communication with the backend Import/Export endpoints."""

    @staticmethod
    def _get_headers():
        """Helper to get auth headers for the httpx endpoints."""
        token = app.storage.user.get("token")
        return {"Authorization": f"Bearer {token}"} if token else {}

    @classmethod
    async def fetch_all(cls, entity: str):
        """Generic fetch to pull the base table elements, paginating to respect backend limits."""
        all_items = []
        skip = 0
        limit = 100

        while True:
            data = await cls.get(f"/{entity}/?skip={skip}&limit={limit}")

            if data:
                current_batch = []
                if isinstance(data, dict):
                    for key, val in data.items():
                        if isinstance(val, list):
                            current_batch = val
                            break
                elif isinstance(data, list):
                    current_batch = data

                if not current_batch:
                    break

                all_items.extend(current_batch)

                if len(current_batch) < limit:
                    break

                skip += limit
            else:
                break

        return all_items

    @classmethod
    async def export_csv(cls, entity: str, ids: list[int]):
        """Requests the bulk export from the backend and triggers a local file download."""
        # Using httpx directly because APIClient expects JSON responses, not raw CSV files
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(
                    f"{BASE_URL}/import_export/export/{entity}",
                    json={"ids": ids},
                    headers=cls._get_headers(),
                )
            except httpx.HTTPError:
                ui.notify("Server did not respond in time.", type="negative")
                return []
            if res.status_code == 200:
                ui.download(res.content, f"{entity}_export.csv")
                ui.notify(
                    f"Successfully exported {len(ids)} {entity}.", type="positive"
                )
            else:
                ui.notify(
                    f"Export failed. Could not retrieve CSV data.", type="negative"
                )

    @classmethod
    async def validate_import(cls, entity: str, file_bytes: bytes):
        """Sends raw CSV bytes to the backend for relational conflict validation."""
        # Using httpx directly because APIClient likely doesn't support 'files=' multipart uploads
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"file": ("upload.csv", file_bytes, "text/csv")}
            try:
                res = await client.post(
                    f"{BASE_URL}/import_export/validate/{entity}",
                    files=files,
                    headers=cls._get_headers(),
                )
            except httpx.HTTPError:
                ui.notify("Server did not respond in time.", type="negative")
                return []
            if res.status_code == 200:
                return res.json()

            ui.notify(f"Validation failed: {_detail(res)}", type="negative")
            return []

    @classmethod
    async def commit_import(
        cls, entity: str, actions: list, batch_id: str | None = None
    ):
        try:
            res = await cls.post(
                f"/import_export/commit/{entity}",
                data={"actions": actions, "batch_id": batch_id},
                timeout=120.0,
            )
        except httpx.ReadTimeout:
            ui.notify(
                "The server is still processing this import. Don't re-upload; check the data in a minute.",
                type="warning",
            )
            return False
        except httpx.HTTPStatusError as e:
            ui.notify(f"Commit failed: {_detail(e.response)}", type="negative")
            return False
        if res:
            ui.notify(
                f"{entity.capitalize()} import completed successfully!", type="positive"
            )
            return True
        ui.notify("Commit failed.", type="negative")
        return False
