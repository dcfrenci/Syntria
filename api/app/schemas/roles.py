from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, examples=["Admin"])


class RoleCreate(RoleBase):
    pass


class RoleResponse(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)