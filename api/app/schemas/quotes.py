from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.persons import PersonResponse
from app.schemas.items import ItemResponse

QuoteStatus = Literal["Draft", "Pending", "Accepted", "Rejected"]

class QuoteItemBase(BaseModel):
    item_id: int = Field(..., description="ID of the selected Item/Service")
    quantity: int = Field(default=1, gt=0)
    discount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)

class QuoteItemCreate(QuoteItemBase):
    pass

class QuoteItemResponse(QuoteItemBase):
    id: int
    unit_price: Decimal
    item: ItemResponse
    
    model_config = ConfigDict(from_attributes=True)

class QuoteBase(BaseModel):
    valid_until: date | None = None

class QuoteCreate(QuoteBase):
    patient_id: int
    staff_id: int | None = Field(default=None, description="The dentist creating the quote")
    items: list[QuoteItemCreate] = Field(..., min_length=1, description="List of services in this quote")

class QuoteUpdate(BaseModel):
    status: QuoteStatus | None = None
    valid_until: date | None = None

class QuoteResponse(QuoteBase):
    id: int
    status: QuoteStatus
    total_amount: Decimal
    patient: PersonResponse
    staff: PersonResponse | None = None
    quote_items: list[QuoteItemResponse]
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class QuoteListResponse(BaseModel):
    total: int
    quotes: list[QuoteResponse]