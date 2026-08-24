from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import Role, User, Person
from app.routers.auth import get_current_user
from app.schemas.roles import RoleCreate, RoleResponse
from app.schemas.users import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users & Staff"])

# ---------------------------------------------------------
# Bootstrap Endpoints
# ---------------------------------------------------------
@router.post("/bootstrap_user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap_first_admin(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    count = (await db.execute(select(func.count(User.id)))).scalar_one()
    if count > 0:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Bootstrap already completed.")
    # ... same creation logic as create_user, minus the current_user dependency
    
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


@router.post("/bootstrap_role", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
):  
    count = (await db.execute(select(func.count(Role.id)))).scalar_one()
    if count > 0:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Bootstrap already completed.")
    
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


# ---------------------------------------------------------
# User (Staff Account) CRUD Endpoints
# ---------------------------------------------------------
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of the currently logged-in staff member."""
    return current_user


@router.get("/", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    role_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
):
    filters = []
    if role_id is not None:
        filters.append(User.role_id == role_id)
    if is_active is not None:
        filters.append(User.is_active == is_active)

    query = (
        select(User)
        .options(selectinload(User.person), selectinload(User.role))
    )
    count_query = select(func.count(User.id))

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    total = (await db.execute(count_query)).scalar_one()
    users = (
        await db.execute(
            query.order_by(User.id).offset(skip).limit(limit)
        )
    ).scalars().all()

    return {"total": total, "users": users}


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    return user


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    await db.refresh(user, ["person", "role"])
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found.",
        )

    await db.delete(user)
    return None