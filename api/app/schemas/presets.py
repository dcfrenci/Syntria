from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class ComponentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    QUOTE = "quote"
    SIGN = "sign"

class MarginSchema(BaseModel):
    top: float = Field(default=96.0)
    right: float = Field(default=96.0)
    bottom: float = Field(default=96.0)
    left: float = Field(default=96.0)

class ComponentSchema(BaseModel):
    id: str = Field(..., description="UUID from the frontend")
    type: ComponentType = Field(..., description="Strictly validated component type")
    x: float
    y: float
    w: float
    h: float
    content: str | None = None

class PresetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = Field(default=False)
    elements: list[ComponentSchema] = Field(default_factory=list)
    margins: MarginSchema = Field(default_factory=MarginSchema)

class PresetCreate(PresetBase):
    pass

class PresetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None
    elements: list[ComponentSchema] | None = None
    margins: MarginSchema | None = None

class PresetResponse(PresetBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)

class PresetListResponse(BaseModel):
    total: int
    presets: list[PresetResponse]