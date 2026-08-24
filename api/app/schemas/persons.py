from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.schemas.reminders import ReminderPreferenceResponse


# --- Person Schemas ---
class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, examples=["Mario"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Rossi"])
    email: EmailStr = Field(..., examples=["mario.rossi@example.com"])
    birth_date: date | None = Field(default=None, examples=["1985-06-15"])
    phone_number: str | None = Field(default=None, max_length=20, examples=["+393331234567"])
    reminder_preference_id: int | None = Field(default=None, examples=[1])


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    birth_date: date | None = None
    phone_number: str | None = Field(default=None, max_length=20)
    reminder_preference_id: int | None = None


class PersonResponse(PersonBase):
    id: int
    reminder_preference: ReminderPreferenceResponse | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class PersonListResponse(BaseModel):
    total: int
    persons: list[PersonResponse]