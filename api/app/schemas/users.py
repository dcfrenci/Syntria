from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from app.schemas.persons import PersonResponse
from app.schemas.roles import RoleResponse


class SystemBootstrap(BaseModel):
    role_name: str = Field(
        default="Admin", description="Name of the initial admin role"
    )
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone_number: str | None = Field(default=None, max_length=20)
    birth_date: date | None = None


class UserBase(BaseModel):
    person_id: int = Field(
        ..., description="ID of the Person this login belongs to", examples=[1]
    )
    role_id: int = Field(..., description="ID of the assigned Role", examples=[1])
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    password: str = Field(
        ..., min_length=8, description="Plaintext password to hash on creation"
    )


class UserUpdate(BaseModel):
    role_id: int | None = None
    is_active: bool | None = None
    password: str | None = Field(
        default=None, min_length=8, description="Update password if provided"
    )


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
