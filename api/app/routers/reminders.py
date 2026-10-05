from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import ReminderPreference, User
from app.routers.auth import RoleChecker
from app.schemas.reminders import (
    ReminderPreferenceCreate,
    ReminderPreferenceResponse,
)

router = APIRouter(prefix="/reminders", tags=["Reminders"])

allow_read = RoleChecker(
    ["admin", "manager", "secretary", "doctor", "assistant", "client"]
)
allow_admin = RoleChecker(["admin"])


@router.get("/", response_model=list[ReminderPreferenceResponse])
async def list_reminder_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_read),
):
    result = await db.execute(
        select(ReminderPreference).order_by(ReminderPreference.name)
    )
    return result.scalars().all()


@router.post(
    "/", response_model=ReminderPreferenceResponse, status_code=status.HTTP_201_CREATED
)
async def create_reminder_preference(
    payload: ReminderPreferenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_admin),
):
    query = select(ReminderPreference).where(
        ReminderPreference.name.ilike(payload.name)
    )
    if (await db.execute(query)).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Reminder preference '{payload.name}' already exists.",
        )

    pref = ReminderPreference(**payload.model_dump())
    db.add(pref)
    await db.flush()
    return pref
