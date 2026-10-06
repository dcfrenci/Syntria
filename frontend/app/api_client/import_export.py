import os
import httpx
from nicegui import app, ui
from api_client.base import APIClient

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

class DataClient(APIClient):
    """Manages communication with the backend Import/Export endpoints."""

    @staticmethod
    def _get_headers():
        """Helper to get auth headers for the httpx endpoints."""
        token = app.storage.user.get('token')
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
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{BASE_URL}/import_export/export/{entity}",
                json={"ids": ids},
                headers=cls._get_headers()
            )
            if res.status_code == 200:
                ui.download(res.content, f"{entity}_export.csv")
                ui.notify(f"Successfully exported {len(ids)} {entity}.", type='positive')
            else:
                ui.notify(f"Export failed. Could not retrieve CSV data.", type='negative')

    @classmethod
    async def validate_import(cls, entity: str, file_bytes: bytes):
        """Sends raw CSV bytes to the backend for relational conflict validation."""
        # Using httpx directly because APIClient likely doesn't support 'files=' multipart uploads
        async with httpx.AsyncClient() as client:
            files = {"file": ("upload.csv", file_bytes, "text/csv")}
            res = await client.post(
                f"{BASE_URL}/import_export/validate/{entity}",
                files=files,
                headers=cls._get_headers()
            )
            if res.status_code == 200:
                return res.json()
            
            ui.notify("Validation failed. Check console for details.", type='negative')
            return []

    @classmethod
    async def commit_import(cls, entity: str, actions: list):
        """Pushes user-resolved conflicts back to the backend to bulk commit the changes."""
        # Standard JSON endpoint: safe to use APIClient. Fixed 'json=' to 'data='
        res = await cls.post(f"/import_export/commit/{entity}", data={"actions": actions})
        
        if res:
            ui.notify(f"{entity.capitalize()} import completed successfully!", type='positive')
            return True
            
        ui.notify("Commit failed. Check console for details.", type='negative')
        return False