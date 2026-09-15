from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Item, Category
from app.schemas.items import ItemCreate, ItemListResponse, ItemResponse, ItemUpdate

router = APIRouter(prefix="/items", tags=["Items"])


# 1. CREATE
@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: ItemCreate,
    db: AsyncSession = Depends(get_db),
):
    cat_exists = None
    
    # Validate category exists if provided
    if payload.category_id is not None:
        cat_exists = await db.get(Category, payload.category_id)
        if not cat_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category ID {payload.category_id} does not exist."
            )

    # Check duplicate name
    existing_item = (await db.execute(select(Item).where(Item.name == payload.name))).scalar_one_or_none()
    if existing_item:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An item with name '{payload.name}' already exists."
        )

    new_item = Item(**payload.model_dump())
    db.add(new_item)
    await db.flush()
    await db.refresh(new_item)
    return new_item


# 2. READ ALL (Filter by category_id)
@router.get("/", response_model=ItemListResponse, status_code=status.HTTP_200_OK)
async def get_items(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1),
    category_id: int | None = Query(default=None, description="Filter by Category ID"),
    is_active: bool | None = Query(default=None),
    is_specific: bool | None = Query(default=None),
):
    filters = []
    if category_id is not None:
        filters.append(Item.category_id == category_id)
    if is_active is not None:
        filters.append(Item.is_active == is_active)
    if is_specific is not None:
        filters.append(Item.is_specific == is_specific)

    count_query = select(func.count(Item.id)).where(*filters)
    total_count = (await db.execute(count_query)).scalar_one()
    
    items_query = (
        select(Item)
        .options(selectinload(Item.category))
        .where(*filters)
        .order_by(Item.id)
        .offset(skip)
    )
    
    if limit is not None:
        items_query = items_query.limit(limit)
    
    items = (await db.execute(items_query)).scalars().all()        

    return {"total": total_count, "items": items}


# 3. UPDATE (PATCH)
@router.patch("/{item_id}", response_model=ItemResponse, status_code=status.HTTP_200_OK)
async def update_item(
    item_id: int,
    payload: ItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    item = (await db.execute(select(Item).options(selectinload(Item.category)).where(Item.id == item_id))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with id {item_id} not found.")

    update_data = payload.model_dump(exclude_unset=True)

    # Validate new category_id if provided
    if "category_id" in update_data and update_data["category_id"] is not None:
        cat_exists = await db.get(Category, update_data["category_id"])
        if not cat_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category ID {update_data['category_id']} does not exist."
            )

    for field, value in update_data.items():
        setattr(item, field, value)

    await db.flush()
    await db.refresh(item)
    return item

# 4. READ ONE
@router.get("/{item_id}", response_model=ItemResponse, status_code=status.HTTP_200_OK)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    item = (
        await db.execute(
            select(Item).options(selectinload(Item.category)).where(Item.id == item_id)
        )
    ).scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Item with id {item_id} not found."
        )

    return item


# 5. DELETE
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    item = await db.get(Item, item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Item with id {item_id} not found."
        )

    await db.delete(item)
    await db.flush()
    
    return None