from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models import Item, Person, Quote, QuoteItem, User
from app.routers.auth import RoleChecker, get_current_user
from app.schemas.quotes import (
    QuoteCreate,
    QuoteItemCreate,
    QuoteListResponse,
    QuoteResponse,
    QuoteUpdate,
)

router = APIRouter(prefix="/quotes", tags=["Quotes"])

allow_write = RoleChecker(["admin", "manager", "secretary", "doctor"])
allow_delete = RoleChecker(["admin", "manager"])
READ_ROLES = {
    "admin",
    "manager",
    "secretary",
    "doctor",
    "assistant",
    "employee",
    "client",
}


def _can_access(quote: Quote, user: User) -> bool:
    """Same visibility rules as the list endpoint."""
    role = user.role.name.lower()
    if role == "admin":
        return True
    if quote.patient and quote.patient.email == settings.ADMIN_EMAIL:
        return False
    if role in {"manager", "secretary"}:
        return True
    if role == "doctor":
        return quote.staff_id == user.person_id
    return quote.patient_id == user.person_id  # assistant / employee / client


async def _build_items(
    db: AsyncSession,
    requested: list[QuoteItemCreate],
    existing_prices: dict[int, Decimal] | None = None,
) -> tuple[list[QuoteItem], Decimal]:
    item_ids = {r.item_id for r in requested}
    rows = (await db.execute(select(Item).where(Item.id.in_(item_ids)))).scalars().all()
    items_map = {i.id: i for i in rows}
    if len(items_map) != len(item_ids):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="One or more Item IDs are invalid."
        )

    built, total = [], Decimal("0.00")
    for r in requested:
        master = items_map[r.item_id]
        # keep the price already quoted to the patient when editing; use today's price for new lines
        unit_price = (existing_prices or {}).get(master.id, master.price)
        line_total = max(unit_price * r.quantity - r.discount, Decimal("0.00"))
        total += line_total
        built.append(
            QuoteItem(
                item_id=master.id,
                quantity=r.quantity,
                unit_price=unit_price,
                discount=r.discount,
                teeth=r.teeth,
            )
        )
    return built, total


async def _load(db: AsyncSession, quote_id: int) -> Quote:
    stmt = (
        select(Quote)
        .where(Quote.id == quote_id)
        .options(selectinload(Quote.quote_items).selectinload(QuoteItem.item))
        .execution_options(populate_existing=True)
    )
    return (await db.execute(stmt)).scalar_one()


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    payload: QuoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_write),
):
    if not await db.get(Person, payload.patient_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Patient not found.")
    if payload.staff_id and not await db.get(Person, payload.staff_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Staff member not found.")
    if (
        current_user.role.name.lower() == "doctor"
        and payload.staff_id != current_user.person_id
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Doctors can only create their own quotes.",
        )

    items, total = await _build_items(db, payload.items)
    quote = Quote(
        patient_id=payload.patient_id,
        staff_id=payload.staff_id,
        valid_until=payload.valid_until,
        status="Draft",
        total_amount=total,
        quote_items=items,
    )
    db.add(quote)
    await db.flush()
    await db.commit()
    return await _load(db, quote.id)


@router.get("/", response_model=QuoteListResponse, status_code=status.HTTP_200_OK)
async def get_quotes(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    patient_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.name.lower()
    if role not in READ_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    query = (
        select(Quote)
        .options(noload(Quote.quote_items))
        .order_by(Quote.created_at.desc())
    )
    count_query = select(func.count(Quote.id))

    if role in ["assistant", "employee", "client"]:
        patient_id = current_user.person_id
    if role == "doctor":
        query = query.where(Quote.staff_id == current_user.person_id)
        count_query = count_query.where(Quote.staff_id == current_user.person_id)
    if patient_id:
        query = query.where(Quote.patient_id == patient_id)
        count_query = count_query.where(Quote.patient_id == patient_id)
    if role != "admin":
        hide = ~Quote.patient.has(Person.email == settings.ADMIN_EMAIL)
        query, count_query = query.where(hide), count_query.where(hide)

    total = (await db.execute(count_query)).scalar_one()
    quotes = (await db.execute(query.offset(skip).limit(limit))).scalars().all()
    return {"total": total, "quotes": quotes}


@router.get("/{quote_id}", response_model=QuoteResponse, status_code=status.HTTP_200_OK)
async def get_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name.lower() not in READ_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    quote = await db.get(Quote, quote_id)
    # 404 (not 403): don't reveal that someone else's quote exists
    if not quote or not _can_access(quote, current_user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Quote not found.")
    return quote


@router.patch(
    "/{quote_id}", response_model=QuoteResponse, status_code=status.HTTP_200_OK
)
async def update_quote(
    quote_id: int,
    payload: QuoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_write),
):
    quote = await db.get(Quote, quote_id)
    if not quote or not _can_access(quote, current_user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Quote not found.")

    update_data = payload.model_dump(exclude_unset=True)
    update_data.pop("items", None)

    if quote.status in ["Accepted", "Rejected"] and "status" in update_data:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot alter the status of a finalized quote.",
        )

    if "patient_id" in update_data:
        if update_data["patient_id"] is None or not await db.get(
            Person, update_data["patient_id"]
        ):
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Patient not found.")
    if update_data.get("staff_id") is not None and not await db.get(
        Person, update_data["staff_id"]
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Staff member not found.")
    if (
        current_user.role.name.lower() == "doctor"
        and "staff_id" in update_data
        and update_data["staff_id"] != current_user.person_id
    ):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Doctors cannot reassign a quote to another doctor.",
        )

    for field, value in update_data.items():
        setattr(quote, field, value)

    if payload.items is not None:
        existing_prices = {qi.item_id: qi.unit_price for qi in quote.quote_items}
        quote.quote_items, quote.total_amount = await _build_items(
            db, payload.items, existing_prices
        )

    await db.flush()
    await db.commit()
    return await _load(db, quote.id)


@router.delete("/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_delete),
):
    quote = await db.get(Quote, quote_id)
    if not quote:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Quote not found.")
    await db.delete(quote)
    await db.commit()
    return None
