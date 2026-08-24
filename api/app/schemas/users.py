from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.persons import PersonResponse
from app.schemas.roles import RoleResponse


class UserBase(BaseModel):
    person_id: int = Field(..., description="ID of the Person this login belongs to", examples=[1])
    role_id: int = Field(..., description="ID of the assigned Role", examples=[1])
    is_active: bool = Field(default=True)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plaintext password to hash on creation")


class UserUpdate(BaseModel):
    role_id: int | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, description="Update password if provided")


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