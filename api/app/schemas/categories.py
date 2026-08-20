from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name:           str = Field(..., min_length=2, max_length=50, examples=["Orthodontics"])
    description:    str | None = Field(default=None, max_length=255, examples=["Teeth alignment and braces"])
    is_active:      bool = Field(default=True, description="Whether the category is available for selection")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name:           str | None = Field(default=None, min_length=2, max_length=50)
    description:    str | None = Field(default=None, max_length=255)
    is_active:      bool | None = None


class CategoryResponse(CategoryBase):
    id:         int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    total:      int
    categories: list[CategoryResponse]