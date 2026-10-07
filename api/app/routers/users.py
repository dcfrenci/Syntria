from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import date, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import Role, User, Person, Reservation
from app.routers.auth import get_current_user, RoleChecker
from app.schemas.roles import RoleCreate, RoleResponse
from app.schemas.users import (
    SystemBootstrap,
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
# Bootstrap Endpoints
# ---------------------------------------------------------
@router.post("/admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_admin(
    payload: SystemBootstrap,
    db: AsyncSession = Depends(get_db),
):
    """Initializes the system by creating the Admin role, person, and user atomically. Locked after first use."""
    count = (await db.execute(select(func.count(User.id)))).scalar_one()
    if count > 0:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="System already initialized."
        )

    # 1. Create Admin Role
    role = Role(name=payload.role_name)
    db.add(role)
    await db.flush()

    # 2. Create Admin Person
    person = Person(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone_number=payload.phone_number,
        birth_date=payload.birth_date,
    )
    db.add(person)
    await db.flush()

    # 3. Create Admin User
    new_user = User(
        person_id=person.id,
        role_id=role.id,
        hashed_password=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(new_user)
    await db.flush()

    await db.refresh(new_user, ["person", "role"])
    return new_user


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


@router.get("/me", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: User = Depends(allow_all_staff),
):
    """Retrieve details of the currently logged-in staff member."""
    return {"total": 1, "users": [current_user]}


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


@router.get("/{user_id}/reservations", response_model=ReservationListResponse)
async def get_user_reservations(
    user_id: int,
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve reservations assigned to a specific staff member/doctor."""

    role = current_user.role.name.lower()
    if role not in ["admin", "manager", "secretary", "doctor"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Insufficient privileges."
        )
    if role == "doctor" and current_user.id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Self-only access permitted."
        )

    # 1. Verify user exists using async syntax
    user_stmt = select(User).where(User.id == user_id)
    result = await db.execute(user_stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Determine date range
    if not end_date:
        active_start = start_date - timedelta(days=start_date.weekday())
        active_end = active_start + timedelta(days=6)
    else:
        active_start = start_date
        active_end = end_date

    # 3. Build and execute the async query
    query = select(Reservation).where(Reservation.staff.any(id=user_id))

    # Filter >= start at midnight
    query = query.where(Reservation.reservation_date >= active_start)

    # Filter < the day AFTER the end date
    query = query.where(Reservation.reservation_date < active_end + timedelta(days=1))

    # Execute and fetch all results
    result = await db.execute(query)
    reservations = result.scalars().all()

    return {"total": len(reservations), "reservations": reservations}
