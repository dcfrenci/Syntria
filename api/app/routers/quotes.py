from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.persons import Person
from app.models.items import Item
from app.models.quotes import Quote, QuoteItem
from app.schemas.quotes import (
    QuoteCreate,
    QuoteListResponse,
    QuoteResponse,
    QuoteUpdate,
)

router = APIRouter(prefix="/quotes", tags=["Quotes"])

@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    payload: QuoteCreate,
    db: AsyncSession = Depends(get_db),
):
    # 1. Verify Patient
    patient = await db.get(Person, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    # 2. Verify Staff (if provided)
    if payload.staff_id:
        staff = await db.get(Person, payload.staff_id)
        if not staff:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff member not found.")

    # 3. Fetch current Item prices and validate they exist
    item_ids = [req_item.item_id for req_item in payload.items]
    items_result = await db.execute(select(Item).where(Item.id.in_(item_ids)))
    items_map = {item.id: item for item in items_result.scalars().all()}

    if len(items_map) != len(set(item_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more Item IDs are invalid.")

    # 4. Construct Quote
    quote = Quote(
        patient_id=payload.patient_id,
        staff_id=payload.staff_id,
        valid_until=payload.valid_until,
        status="Draft",
    )
    db.add(quote)
    await db.flush()  # We flush here so quote gets its primary key 'id' generated

    # 5. Process Quote Items and calculate total
    total_amount = Decimal("0.00")

    for req_item in payload.items:
        master_item = items_map[req_item.item_id]
        unit_price = master_item.price
        
        # Subtotal: (Price * Quantity) - Discount
        line_total = (unit_price * req_item.quantity) - req_item.discount
        if line_total < 0:
            line_total = Decimal("0.00")

        total_amount += line_total

        quote_item = QuoteItem(
            quote_id=quote.id,
            item_id=master_item.id,
            quantity=req_item.quantity,
            unit_price=unit_price,
            discount=req_item.discount,
        )
        db.add(quote_item)

    # 6. Save total amount back to quote
    quote.total_amount = total_amount
    await db.commit() 

    # 7. Eagerly load the relationships to satisfy the QuoteResponse schema
    stmt = (
        select(Quote)
        .where(Quote.id == quote.id)
        .options(
            selectinload(Quote.quote_items).selectinload(QuoteItem.item)
        )
    )
    result = await db.execute(stmt)
    quote_with_relations = result.scalar_one()

    return quote_with_relations


@router.get("/", response_model=QuoteListResponse, status_code=status.HTTP_200_OK)
async def get_quotes(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    patient_id: int | None = Query(default=None),
):
    query = select(Quote).order_by(Quote.created_at.desc())
    count_query = select(func.count(Quote.id))

    if patient_id:
        query = query.where(Quote.patient_id == patient_id)
        count_query = count_query.where(Quote.patient_id == patient_id)

    total = (await db.execute(count_query)).scalar_one()
    quotes = (await db.execute(query.offset(skip).limit(limit))).scalars().all()

    return {"total": total, "quotes": quotes}


@router.get("/{quote_id}", response_model=QuoteResponse, status_code=status.HTTP_200_OK)
async def get_quote(quote_id: int, db: AsyncSession = Depends(get_db)):
    quote = await db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found.")
    return quote


@router.patch("/{quote_id}", response_model=QuoteResponse, status_code=status.HTTP_200_OK)
async def update_quote(
    quote_id: int,
    payload: QuoteUpdate,
    db: AsyncSession = Depends(get_db),
):
    quote = await db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found.")

    update_data = payload.model_dump(exclude_unset=True)
    
    # Optional logic: prevent status changes on already accepted quotes
    if quote.status in ["Accepted", "Rejected"] and "status" in update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Cannot alter the status of a finalized quote."
        )

    for field, value in update_data.items():
        setattr(quote, field, value)

    await db.flush()
    await db.refresh(quote)
    return quote