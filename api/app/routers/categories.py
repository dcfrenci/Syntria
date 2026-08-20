from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Category
from app.schemas.categories import (
    CategoryCreate,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdate,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


# 1. CREATE (POST)
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
):
    query = select(Category).where(Category.name.ilike(payload.name))
    existing = (await db.execute(query)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category '{payload.name}' already exists."
        )

    category = Category(**payload.model_dump())
    db.add(category)
    await db.flush()
    return category


# 2. READ ALL (GET with pagination and active filter)
@router.get("/", response_model=CategoryListResponse, status_code=status.HTTP_200_OK)
async def get_categories(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
):
    query = select(Category)
    count_query = select(func.count(Category.id))

    if is_active is not None:
        query = query.where(Category.is_active == is_active)
        count_query = count_query.where(Category.is_active == is_active)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(Category.name).offset(skip).limit(limit)
    categories = (await db.execute(query)).scalars().all()

    return {"total": total, "categories": categories}


# 3. READ ONE (GET by ID)
@router.get("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
):
    category = (await db.execute(select(Category).where(Category.id == category_id))).scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found."
        )
    return category


# 4. UPDATE (PATCH)
@router.patch("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
async def update_category(
    category_id: int,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
):
    category = (await db.execute(select(Category).where(Category.id == category_id))).scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found."
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Check for name conflict if name is being updated
    if "name" in update_data and update_data["name"].lower() != category.name.lower():
        name_check = await db.execute(
            select(Category).where(
                Category.name.ilike(update_data["name"]),
                Category.id != category_id
            )
        )
        if name_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category '{update_data['name']}' already exists."
            )

    for key, value in update_data.items():
        setattr(category, key, value)

    return category


# 5. DELETE (DELETE)
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
):
    category = (await db.execute(select(Category).where(Category.id == category_id))).scalar_one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found."
        )

    await db.delete(category)
    return None