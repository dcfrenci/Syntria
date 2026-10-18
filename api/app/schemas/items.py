from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.categories import CategoryResponse
from app.schemas._common import reject_null_fields


class ItemBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Dental Cleaning"])
    description: str | None = Field(default=None, max_length=500)
    price: Decimal = Field(..., gt=0, le=Decimal("99999.99"), max_digits=10, decimal_places=2, examples=[80.00])
    category_id: int | None = Field(default=None, description="Foreign Key to Category table", examples=[1])
    is_active: bool = Field(default=True)
    is_specific: bool = Field(default=False)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: Decimal | None = Field(default=None, gt=0, le=Decimal("99999.99"), max_digits=10, decimal_places=2)
    category_id: int | None = None
    is_active: bool | None = None
    is_specific: bool | None = None

    @model_validator(mode="after")
    def _nulls(self):
        return reject_null_fields(self, "name", "price", "is_active", "is_specific")
    

class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None
    category: CategoryResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemListResponse(BaseModel):
    total: int
    items: list[ItemResponse]