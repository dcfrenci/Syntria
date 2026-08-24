from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Role, User
from app.routers.auth import get_current_user
from app.schemas.roles import (
    RoleCreate,
    RoleResponse,
)

router = APIRouter(prefix="/roles", tags=["Roles"])

@router.get("/", response_model=list[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Role).order_by(Role.name))
    return result.scalars().all()


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(select(Role).where(Role.name.ilike(payload.name)))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role '{payload.name}' already exists.",
        )

    role = Role(name=payload.name)
    db.add(role)
    await db.flush()
    return role