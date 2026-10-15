from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.schemas.persons import PersonResponse
from app.schemas.roles import RoleResponse

MIN_PW = 12
MAX_PW_BYTES = 72  # bcrypt limit


def _check_password(v: str | None) -> str | None:
    if v is None:
        return v
    if len(v.encode("utf-8")) > MAX_PW_BYTES:
        raise ValueError(
            f"Password must not exceed {MAX_PW_BYTES} bytes when UTF-8 encoded."
        )
    return v


class UserBase(BaseModel):
    person_id: int = Field(
        ..., description="ID of the Person this login belongs to", examples=[1]
    )
    role_id: int = Field(..., description="ID of the assigned Role", examples=[1])
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=MIN_PW, description="Plaintext password to hash on creation"
    )
    _pw = field_validator("password")(_check_password)


class UserUpdate(BaseModel):
    role_id: int | None = None
    is_active: bool | None = None
    password: str | None = Field(
        default=None, min_length=MIN_PW, description="Update password if provided"
    )
    _pw = field_validator("password")(_check_password)


class UserResponse(BaseModel):
    id: int
    is_active: bool
    role: RoleResponse
    person: PersonResponse
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    total: int
    users: list[UserResponse]
