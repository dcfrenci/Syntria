from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import User, Person, ReminderPreference
from app.routers.auth import get_current_user, RoleChecker
from app.schemas.persons import (
    PersonCreate,
    PersonListResponse,
    PersonResponse,
    PersonUpdate,
)

router = APIRouter(prefix="/persons", tags=["Persons"])

allow_read = RoleChecker(["admin", "manager", "secretary", "doctor", "assistant"])
allow_write = RoleChecker(["admin", "manager", "secretary", "doctor"])
allow_delete = RoleChecker(["admin", "manager"])


@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    payload: PersonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_write),
):
    # Check for email conflict
    email_check = await db.execute(select(Person).where(Person.email == payload.email))
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A person with email '{payload.email}' already exists.",
        )

    # Validate reminder preference if supplied
    if payload.reminder_preference_id:
        pref = await db.get(ReminderPreference, payload.reminder_preference_id)
        if not pref:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reminder preference ID {payload.reminder_preference_id} not found.",
            )

    person = Person(**payload.model_dump())
    db.add(person)
    await db.flush()
    await db.refresh(person, ["reminder_preference"])
    return person


@router.get("/", response_model=PersonListResponse, status_code=status.HTTP_200_OK)
async def get_persons(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(
        default=None, description="Search by name, email, or phone"
    ),
    current_user: User = Depends(allow_read),
):
    filters = []

    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                Person.first_name.ilike(search_pattern),
                Person.last_name.ilike(search_pattern),
                Person.email.ilike(search_pattern),
                Person.phone_number.ilike(search_pattern),
            )
        )

    query = select(Person).options(selectinload(Person.reminder_preference))
    count_query = select(func.count(Person.id))

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    total = (await db.execute(count_query)).scalar_one()
    query = (
        query.order_by(Person.last_name, Person.first_name).offset(skip).limit(limit)
    )
    persons = (await db.execute(query)).scalars().all()

    return {"total": total, "persons": persons}


@router.get(
    "/{person_id}", response_model=PersonResponse, status_code=status.HTTP_200_OK
)
async def get_person(
    person_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.name.lower()
    if role not in ["admin", "manager", "secretary", "doctor", "assistant", "client"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Insufficient privileges."
        )
    if role == "client" and current_user.person_id != person_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Self-only access permitted."
        )

    person = (
        await db.execute(
            select(Person)
            .options(selectinload(Person.reminder_preference))
            .where(Person.id == person_id)
        )
    ).scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found.",
        )
    return person


@router.patch(
    "/{person_id}", response_model=PersonResponse, status_code=status.HTTP_200_OK
)
async def update_person(
    person_id: int,
    payload: PersonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    role = current_user.role.name.lower()
    if role not in ["admin", "manager", "secretary", "doctor", "client"]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Insufficient privileges."
        )
    if role == "client" and current_user.person_id != person_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Self-only access permitted."
        )

    person = (
        await db.execute(
            select(Person)
            .options(selectinload(Person.reminder_preference))
            .where(Person.id == person_id)
        )
    ).scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Validate email uniqueness if changing email
    if "email" in update_data and update_data["email"] != person.email:
        email_collision = await db.execute(
            select(Person).where(
                Person.email == update_data["email"], Person.id != person_id
            )
        )
        if email_collision.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{update_data['email']}' is already in use.",
            )

    # Validate reminder preference if updating
    if (
        "reminder_preference_id" in update_data
        and update_data["reminder_preference_id"] is not None
    ):
        pref = await db.get(ReminderPreference, update_data["reminder_preference_id"])
        if not pref:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reminder preference ID {update_data['reminder_preference_id']} not found.",
            )

    for field, value in update_data.items():
        setattr(person, field, value)

    await db.flush()
    await db.refresh(person, ["reminder_preference"])
    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_delete),
):
    person = await db.get(Person, person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found.",
        )

    await db.delete(person)
    return None
