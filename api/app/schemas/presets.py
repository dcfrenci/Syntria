import re
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_ELEMENTS = 100
MAX_IMAGE_CHARS = 3_000_000  # ~2 MB binary after base64
MAX_TEXT_CHARS = 5_000
_IMG_RE = re.compile(r"^data:image/(?:png|jpeg|gif|webp);base64,[A-Za-z0-9+/=]+$")


class ComponentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    QUOTE = "quote"
    SIGN = "sign"
    CLIENT = "client"
    DATE = "date"


class MarginSchema(BaseModel):
    top: float = Field(default=96.0, ge=0, le=1123)
    right: float = Field(default=96.0, ge=0, le=794)
    bottom: float = Field(default=96.0, ge=0, le=1123)
    left: float = Field(default=96.0, ge=0, le=794)


class ComponentSchema(BaseModel):
    id: str = Field(..., max_length=64, description="UUID from the frontend")
    type: ComponentType = Field(..., description="Strictly validated component type")
    x: float
    y: float
    w: float
    h: float
    content: str | None = None
    font_size: int | None = Field(default=None, ge=1, le=200)
    font_bold: bool | None = None
    font_italic: bool | None = None
    image_fit: str | None = Field(default=None, pattern="^(contain|cover)$")
    image_pos_x: float | None = None
    image_pos_y: float | None = None

    @model_validator(mode="after")
    def _validate_content(self):
        if self.content is None:
            return self
        if self.type == ComponentType.IMAGE:
            # Only base64 raster images: no quotes/URLs/SVG can break out of the <img src="..."> attribute
            if len(self.content) > MAX_IMAGE_CHARS or not _IMG_RE.match(self.content):
                raise ValueError("Image content must be a PNG/JPEG/GIF/WebP base64 data URI under ~2 MB.")
        elif len(self.content) > MAX_TEXT_CHARS:
            raise ValueError("Content too long.")
        return self


class PresetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = Field(default=False)
    elements: list[ComponentSchema] = Field(default_factory=list, max_length=MAX_ELEMENTS)
    margins: MarginSchema = Field(default_factory=MarginSchema)


class PresetCreate(PresetBase):
    pass


class PresetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None
    elements: list[ComponentSchema] | None = Field(default=None, max_length=MAX_ELEMENTS)
    margins: MarginSchema | None = None


class PresetResponse(PresetBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PresetSummary(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PresetListResponse(BaseModel):  # (the duplicate, dead definition was removed)
    total: int
    presets: list[PresetSummary]