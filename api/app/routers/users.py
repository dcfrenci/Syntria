from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Person, Reservation, Role, User
from app.routers.auth import RoleChecker, get_current_user
from app.schemas.reservations import ReservationListResponse
from app.schemas.users import UserCreate, UserListResponse, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users & Staff"])

allow_admin_mgr = RoleChecker(["admin", "manager"])
allow_admin_mgr_sec = RoleChecker(["admin", "manager", "secretary"])
allow_all_staff = RoleChecker(
    ["admin", "manager", "secretary", "doctor", "assistant", "employee"]
)

ROLE_RANK = {
    "admin": 0,
    "manager": 1,
    "secretary": 2,
    "doctor": 2,
    "assistant": 2,
    "employee": 3,
    "client": 4,
}


def _rank(role_name: str) -> int:
    return ROLE_RANK.get(role_name.lower(), 99)


# ---------------------------------------------------------
# Privilege helpers
# ---------------------------------------------------------
def _is_admin(u: User) -> bool:
    return u.role.name.lower() == "admin"


async def _active_admin_count(db: AsyncSession) -> int:
    q = (
        select(func.count(User.id))
        .join(User.role)
        .where(func.lower(Role.name) == "admin", User.is_active.is_(True))
    )
    return (await db.execute(q)).scalar_one()


async def _guard(
    db: AsyncSession,
    actor: User,
    *,
    target: User | None = None,
    new_role_id: int | None = None,
) -> None:
    """Only an admin may touch an admin account or hand out the Admin role."""
    if _is_admin(actor):
        return
    me = _rank(actor.role.name)
    if target is not None and target.id != actor.id and _rank(target.role.name) <= me:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You can only modify accounts with a lower role than yours.",
        )
    if new_role_id is not None:
        role = await db.get(Role, new_role_id)
        if role and _rank(role.name) <= me:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="You can only assign roles lower than your own.",
            )


# ---------------------------------------------------------
# CRUD
# ---------------------------------------------------------
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_admin_mgr),
):
    await _guard(db, current_user, new_role_id=payload.role_id)  # <-- NEW

    person = await db.get(Person, payload.person_id)
    if not person:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Person ID {payload.person_id} not found.",
        )

    user_check = await db.execute(
        select(User).where(User.person_id == payload.person_id)
    )
    if user_check.scalar_one_or_none():
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="A staff user account is already linked to this person.",
        )

    role = await db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Role ID {payload.role_id} not found."
        )

    new_user = User(
        person_id=payload.person_id,
        role_id=payload.role_id,
        hashed_password=await asyncio.to_thread(get_password_hash, payload.password),
        is_active=payload.is_active,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user, ["person", "role"])
    return new_user


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(current_user: User = Depends(allow_all_staff)):
    """Retrieve details of the currently logged-in staff member."""
    return current_user


@router.get("/", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def list_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    role: str | None = Query(default=None, max_length=50),
    role_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(allow_admin_mgr_sec),
):
    filters = []
    if role_id is not None:
        filters.append(User.role_id == role_id)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    if role:
        filters.append(User.role.has(func.lower(Role.name) == role.lower()))
    if not _is_admin(current_user):
        filters.append(User.role.has(func.lower(Role.name) != "admin"))

    query = select(User).options(selectinload(User.person), selectinload(User.role))
    count_query = select(func.count(User.id))
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    total = (await db.execute(count_query)).scalar_one()
    users = (
        (await db.execute(query.order_by(User.id).offset(skip).limit(limit)))
        .scalars()
        .all()
    )
    return {"total": total, "users": users}


@router.get("/reservations", response_model=ReservationListResponse)
async def get_reservations(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(
        None,
        description="End date (YYYY-MM-DD). Default: the Mon-Sun week of start_date",
    ),
    user_id: Optional[int] = Query(
        None,
        description="PERSON id to look up (doctor or patient). Default: the logged-in user's person.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reservations where the target person is staff or patient."""
    role = current_user.role.name.lower()
    privileged_roles = ["admin", "manager", "secretary"]
    standard_roles = ["doctor", "assistant", "employee", "client"]

    if role not in privileged_roles + standard_roles:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Insufficient privileges."
        )

    target_person_id = user_id if user_id is not None else current_user.person_id

    if target_person_id != current_user.person_id:
        if role not in privileged_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="You can only view your own reservations.",
            )
        target = await db.get(Person, target_person_id)
        if target is None or (target.email == settings.ADMIN_EMAIL and role != "admin"):
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="Target person not found."
            )

    if end_date is None:
        active_start = start_date - timedelta(days=start_date.weekday())
        active_end = active_start + timedelta(days=6)
    else:
        active_start, active_end = start_date, end_date

    range_start = datetime.combine(active_start, time.min, tzinfo=timezone.utc)
    range_end = datetime.combine(
        active_end + timedelta(days=1), time.min, tzinfo=timezone.utc
    )

    query = (
        select(Reservation)
        .where(
            or_(
                Reservation.staff.any(id=target_person_id),
                Reservation.patient_id == target_person_id,
            ),
            Reservation.reservation_date >= range_start,
            Reservation.reservation_date < range_end,
        )
        .order_by(Reservation.reservation_date)
    )
    reservations = (await db.execute(query)).scalars().unique().all()
    return {"total": len(reservations), "reservations": reservations}


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.name.lower()
    if role not in ["admin", "manager", "secretary", "doctor"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Insufficient privileges."
        )
    if role == "doctor" and current_user.id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Self-only access permitted."
        )

    user = (
        await db.execute(
            select(User)
            .options(selectinload(User.person), selectinload(User.role))
            .where(User.id == user_id)
        )
    ).scalar_one_or_none()

    # NEW: 404 (not 403) so non-admins can't even confirm an admin account exists
    if not user or (_is_admin(user) and not _is_admin(current_user)):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found."
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_admin_mgr),
):
    user = (
        await db.execute(
            select(User)
            .options(selectinload(User.person), selectinload(User.role))
            .where(User.id == user_id)
        )
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found."
        )

    update_data = payload.model_dump(exclude_unset=True)

    await _guard(
        db, current_user, target=user, new_role_id=update_data.get("role_id")
    )  # <-- NEW

    new_role = None
    if update_data.get("role_id") is not None:
        new_role = await db.get(Role, update_data["role_id"])
        if not new_role:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"Role ID {update_data['role_id']} not found.",
            )

    # NEW: never lock the system out of its last admin, never let someone deactivate themselves
    if update_data.get("is_active") is False and user.id == current_user.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )
    loses_admin = (
        _is_admin(user)
        and user.is_active
        and (
            update_data.get("is_active") is False
            or (new_role is not None and new_role.name.lower() != "admin")
        )
    )
    if loses_admin and await _active_admin_count(db) <= 1:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote or deactivate the last active admin.",
        )

    if update_data.get("password"):
        user.hashed_password = await asyncio.to_thread(
            get_password_hash, update_data.pop("password")
        )
    else:
        update_data.pop("password", None)

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(RoleChecker(["admin"])),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"User with ID {user_id} not found."
        )
    if user.id == current_user.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account."
        )
    if _is_admin(user) and user.is_active and await _active_admin_count(db) <= 1:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Cannot delete the last active admin."
        )

    await db.delete(user)
    return None
