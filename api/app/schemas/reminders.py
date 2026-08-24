from pydantic import BaseModel, ConfigDict, EmailStr, Field

class ReminderPreferenceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, examples=["WhatsApp"])


class ReminderPreferenceCreate(ReminderPreferenceBase):
    pass


class ReminderPreferenceResponse(ReminderPreferenceBase):
    id: int

    model_config = ConfigDict(from_attributes=True)