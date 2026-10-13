from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import Role, User, Person, Reservation
from app.routers.auth import get_current_user, RoleChecker
from app.schemas.users import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.schemas.reservations import ReservationListResponse

router = APIRouter(prefix="/users", tags=["Users & Staff"])

allow_admin_mgr = RoleChecker(["admin", "manager"])
allow_admin_mgr_sec = RoleChecker(["admin", "manager", "secretary"])
allow_all_staff = RoleChecker(
    ["admin", "manager", "secretary", "doctor", "assistant", "employee"]
)


# ---------------------------------------------------------
# User (Staff Account) CRUD Endpoints
# ---------------------------------------------------------
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_admin_mgr),
):
    # 1. Check if Person exists
    person = await db.get(Person, payload.person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person ID {payload.person_id} not found.",
        )

    # 2. Check if Person already has a User account
    user_check = await db.execute(
        select(User).where(User.person_id == payload.person_id)
    )
    if user_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A staff user account is already linked to this person.",
        )

    # 3. Check if Role exists
    role = await db.get(Role, payload.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role ID {payload.role_id} not found.",
        )

    # 4. Create User with hashed password
    new_user = User(
        person_id=payload.person_id,
        role_id=payload.role_id,
        hashed_password=get_password_hash(payload.password),
        is_active=payload.is_active,
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user, ["person", "role"])
    return new_user


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: User = Depends(allow_all_staff),
):
    """Retrieve details of the currently logged-in staff member."""
    return current_user


@router.get("/", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def list_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    role_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    current_user: User = Depends(allow_admin_mgr_sec),
):
    filters = []
    if role_id is not None:
        filters.append(User.role_id == role_id)
    if is_active is not None:
        filters.append(User.is_active == is_active)

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
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD). Default: the Mon-Sun week of start_date"),
    user_id: Optional[int] = Query(None, description="PERSON id to look up (doctor or patient). Default: the logged-in user's person."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reservations where the target person is staff or patient."""
    role = current_user.role.name.lower()
    privileged_roles = ["admin", "manager", "secretary"]
    standard_roles = ["doctor", "assistant", "employee", "client"]

    if role not in privileged_roles + standard_roles:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Insufficient privileges.")

    target_person_id = user_id if user_id is not None else current_user.person_id

    if target_person_id != current_user.person_id:
        if role not in privileged_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="You can only view your own reservations."
            )
        if await db.get(Person, target_person_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Target person not found.")

    if end_date is None:
        active_start = start_date - timedelta(days=start_date.weekday())
        active_end = active_start + timedelta(days=6)
    else:
        active_start, active_end = start_date, end_date

    # explicit tz-aware bounds, end exclusive
    range_start = datetime.combine(active_start, time.min, tzinfo=timezone.utc)
    range_end = datetime.combine(active_end + timedelta(days=1), time.min, tzinfo=timezone.utc)

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

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # If updating role, ensure target role exists
    if "role_id" in update_data and update_data["role_id"] is not None:
        role = await db.get(Role, update_data["role_id"])
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role ID {update_data['role_id']} not found.",
            )

    # Hash new password if updated
    if "password" in update_data and update_data["password"]:
        user.hashed_password = get_password_hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"])),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    await db.delete(user)
    return None
