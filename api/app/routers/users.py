from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import date, timedelta
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

@router.get("/reservations", response_model=ReservationListResponse)
async def get_reservations(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    user_id: Optional[int] = Query(None, description="Optional ID of the user to look up. Defaults to current user."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve reservations for the logged-in user, or a specific user if requested by an admin."""

    role = current_user.role.name.lower()
    privileged_roles = ["admin", "manager", "secretary"]
    standard_roles = ["doctor", "assistant", "employee", "client"]

    if role not in privileged_roles + standard_roles:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Insufficient privileges."
        )

    # 1. Determine which ID we are looking up
    # If the user didn't provide an ID, assume they want their own schedule
    target_id = user_id if user_id is not None else current_user.id

    # 2. Access Control Check
    # If a standard user is trying to look up an ID that isn't theirs, block it
    if target_id != current_user.id and role not in privileged_roles:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="You can only view your own reservations."
        )

    # 3. Verify target user exists (only strictly necessary if user_id was provided)
    if target_id != current_user.id:
        user_stmt = select(User).where(User.id == target_id)
        result = await db.execute(user_stmt)
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="Target user not found")

    # 4. Determine date range
    if not end_date:
        active_start = start_date - timedelta(days=start_date.weekday())
        active_end = active_start + timedelta(days=6)
    else:
        active_start = start_date
        active_end = end_date

    # 5. Build and execute the async query for the target_id
    query = select(Reservation).where(
        or_(
            Reservation.staff.any(id=target_id),
            Reservation.patient_id == target_id
        )
    )

    query = query.where(Reservation.reservation_date >= active_start)
    query = query.where(Reservation.reservation_date < active_end + timedelta(days=1))

    result = await db.execute(query)
    reservations = result.scalars().unique().all()

    return {"total": len(reservations), "reservations": reservations}



# @router.get("/{user_id}/reservations", response_model=ReservationListResponse)
# async def get_user_reservations(
#     user_id: int,
#     start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
#     end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """Retrieve reservations assigned to a specific staff member or patient."""

#     role = current_user.role.name.lower()
#     privileged_roles = ["admin", "manager", "secretary"]
#     standard_roles = ["doctor", "assistant", "employee", "client"]
    
#     print(f"user_id: {user_id}, current_user_id: {current_user.id}", flush=True)

#     if role not in privileged_roles + standard_roles:
#         raise HTTPException(
#             status.HTTP_403_FORBIDDEN, detail="Insufficient privileges."
#         )
        
#     # Standard users can only view their own reservations
#     if role in standard_roles and current_user.id != user_id:
#         raise HTTPException(
#             status.HTTP_403_FORBIDDEN, detail="Self-only access permitted."
#         )

#     # 1. Verify user exists using async syntax
#     user_stmt = select(User).where(User.id == user_id)
#     result = await db.execute(user_stmt)
#     user = result.scalars().first()

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # 2. Determine date range
#     if not end_date:
#         active_start = start_date - timedelta(days=start_date.weekday())
#         active_end = active_start + timedelta(days=6)
#     else:
#         active_start = start_date
#         active_end = end_date

#     # 3. Build and execute the async query
#     # Match if the user is either assigned as staff OR is the patient
#     query = select(Reservation).where(
#         or_(
#             Reservation.staff.any(id=user_id),
#             Reservation.patient_id == user_id
#         )
#     )

#     # Filter >= start at midnight
#     query = query.where(Reservation.reservation_date >= active_start)

#     # Filter < the day AFTER the end date
#     query = query.where(Reservation.reservation_date < active_end + timedelta(days=1))

#     # Execute and fetch all results
#     result = await db.execute(query)
#     reservations = result.scalars().unique().all() # Add .unique() when using joined queries/any()

#     return {"total": len(reservations), "reservations": reservations}
