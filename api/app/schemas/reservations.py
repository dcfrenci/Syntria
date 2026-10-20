from datetime import datetime
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from app.schemas._common import reject_null_fields

from app.schemas.persons import PersonResponse


class ReservationBase(BaseModel):
    reservation_date: AwareDatetime = Field(
        ..., description="Date and time of the reservation"
    )
    duration_minutes: int = Field(
        default=30, gt=0, le=1440, description="Duration in minutes"
    )
    description: str | None = Field(
        default=None, max_length=500, description="Notes about the visit"
    )


class ReservationCreate(ReservationBase):
    patient_id: int = Field(..., description="ID of the patient")
    staff_ids: list[int] = Field(
        ..., min_length=1, description="At least one staff member required"
    )


class ReservationUpdate(BaseModel):
    reservation_date: AwareDatetime | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    description: str | None = Field(default=None, max_length=500)
    patient_id: int | None = None
    staff_ids: list[int] | None = Field(
        default=None, min_length=1, description="Overwrite assigned staff"
    )

    @model_validator(mode="after")
    def _nulls(self):
        return reject_null_fields(
            self, "reservation_date", "duration_minutes", "patient_id", "staff_ids"
        )


class ReservationResponse(ReservationBase):
    id: int
    patient: PersonResponse
    staff: list[PersonResponse]
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ReservationListResponse(BaseModel):
    total: int
    reservations: list[ReservationResponse]
