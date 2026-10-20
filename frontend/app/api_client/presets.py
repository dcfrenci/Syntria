from api_client.base import APIClient

class PresetsClient:
    
    @staticmethod
    async def get_presets():
        """Fetches all presets."""
        result = await APIClient.get("/presets/")
        return result.get("presets", []) if result else []
    
    @staticmethod
    async def get_active_preset():
        """Fetche active preset."""
        return await APIClient.get("/presets/active")

    @staticmethod
    async def get_preset(preset_id: int):
        """Fetches the preset with a specific id."""
        return await APIClient.get(f"/presets/{preset_id}")

    @staticmethod
    async def create_preset(data: dict):
        """Creates a new preset."""
        return await APIClient.post("/presets/", data=data)

    @staticmethod
    async def update_preset(preset_id: int, data: dict):
        """Updates the preset with a specific id."""
        return await APIClient.patch(f"/presets/{preset_id}", data=data)
    
    @staticmethod
    async def upload_image(content: bytes, filename: str) -> str:
        """Returns the element content reference, e.g. 'image:12'."""
        res = await APIClient.post_file("/presets/images", files={"file": (filename, content)})
        return res["content"]

    @staticmethod
    async def delete_preset(preset_id: int):
        """Deletes the preset with a specific id."""
        return await APIClient.delete(f"/presets/{preset_id}")