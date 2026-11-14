from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.services.privileges import _guard, _is_admin, _active_admin_count
from app.models import User, Person, ReminderPreference, Quote, Reservation
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


def _hide_admin(person: Person, actor: User) -> None:
    """Non-admins must not see, edit or delete the system admin's Person record."""
    if person.email.lower() == settings.ADMIN_EMAIL.lower() and actor.role.name.lower() != "admin":
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Person not found.")


@router.post("/", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    payload: PersonCreate,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_write),
):
    email = payload.email.lower()
    exists = await db.execute(select(Person.id).where(func.lower(Person.email) == email))
    if exists.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A person with email '{email}' already exists.",
        )

    if payload.reminder_preference_id:
        pref = await db.get(ReminderPreference, payload.reminder_preference_id)
        if not pref:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Reminder preference ID {payload.reminder_preference_id} not found.",
            )

    payload_data = {**payload.model_dump(), "email": email}
    person = Person(**payload_data)
    db.add(person)
    await db.flush()
    await db.refresh(person, ["reminder_preference"])
    return person


@router.get("/", status_code=status.HTTP_200_OK)
async def get_persons(
    db: AsyncSession = Depends(get_db, scope="function"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(
        default=None, description="Search by name, email, or phone", max_length=100
    ),
    current_user: User = Depends(allow_read),
):
    role = current_user.role.name.lower()
    is_restricted = role in ("doctor", "assistant")

    # Restrict doctors and assistants to targeted searches
    if is_restricted:
        if not search or len(search.strip()) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Search term (min 3 chars) required."
            )
        limit = min(limit, 20)

    filters = []

    if search:
        for token in search.split()[:5]:
            esc = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pat = f"%{esc}%"
            filters.append(
                or_(
                    Person.first_name.ilike(pat, escape="\\"),
                    Person.last_name.ilike(pat, escape="\\"),
                    Person.email.ilike(pat, escape="\\"),
                    Person.phone_number.ilike(pat, escape="\\"),
                )
            )

    if role != "admin":
        filters.append(func.lower(Person.email) != settings.ADMIN_EMAIL.lower())

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

    # Return brief schema and audit the read for restricted roles
    if is_restricted:
        # Assuming an AuditLog model exists in your models directory
        from app.models import AuditLog 
        
        audit_entry = AuditLog(
            user_id=current_user.id,
            action="SEARCH_PERSONS_LIST",
            details=f"Doctor/Assistant searched persons list with term: '{search}'"
        )
        db.add(audit_entry)
        await db.flush()

        # Return a brief schema: id, first_name, last_name
        brief_persons = [
            {"id": p.id, "first_name": p.first_name, "last_name": p.last_name}
            for p in persons
        ]
        return {"total": total, "persons": brief_persons}

    return {"total": total, "persons": persons}


@router.get(
    "/{person_id}", response_model=PersonResponse, status_code=status.HTTP_200_OK
)
async def get_person(
    person_id: int,
    db: AsyncSession = Depends(get_db, scope="function"),
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
    if role in ("doctor", "assistant") and person_id != current_user.person_id:
        related = (
            await db.execute(
                select(Reservation.id)
                .where(
                    Reservation.patient_id == person_id,
                    Reservation.staff.any(id=current_user.person_id),
                )
                .limit(1)
            )
        ).first() or (
            role == "doctor"
            and (
                await db.execute(
                    select(Quote.id)
                    .where(
                        Quote.patient_id == person_id,
                        Quote.staff_id == current_user.person_id,
                    )
                    .limit(1)
                )
            ).first()
        )
        if not related:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Person not found.")

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
    _hide_admin(person, current_user)
    return person


@router.patch(
    "/{person_id}", response_model=PersonResponse, status_code=status.HTTP_200_OK
)
async def update_person(
    person_id: int,
    payload: PersonUpdate,
    db: AsyncSession = Depends(get_db, scope="function"),
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
            .options(
                selectinload(Person.reminder_preference), 
                selectinload(Person.user_account)
            )
            .where(Person.id == person_id)
        )
    ).scalar_one_or_none()

    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found.",
        )
    _hide_admin(person, current_user)

    update_data = payload.model_dump(exclude_unset=True)

    # Privilege guard: Prevent lower roles from changing higher-role login emails
    if person.user_account and person.id != current_user.person_id and "email" in update_data:
        await _guard(db, current_user, target=person.user_account)

    if "email" in update_data:
        update_data["email"] = update_data["email"].lower()

    if (
        person.email.lower() == settings.ADMIN_EMAIL.lower()
        and "email" in update_data
        and update_data["email"] != person.email.lower()
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="The admin email is bound to ADMIN_EMAIL; change it in .env and in the database together.",
        )

    if "email" in update_data and update_data["email"] != person.email.lower():
        email_collision = await db.execute(
            select(Person.id).where(
                func.lower(Person.email) == update_data["email"], Person.id != person_id
            )
        )
        if email_collision.first():
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
    await db.refresh(person)
    await db.refresh(person, ["reminder_preference"])
    return person


@router.delete("/{person_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_person(
    person_id: int,
    db: AsyncSession = Depends(get_db, scope="function"),
    current_user: User = Depends(allow_delete),
):
    person = await db.get(Person, person_id)
    if not person:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"Person with ID {person_id} not found."
        )
    _hide_admin(person, current_user)
    if person.email.lower() == settings.ADMIN_EMAIL.lower():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="The system admin person cannot be deleted.",
        )
    
    # Prevent bypass of admin and rank guards via cascading deletes
    target_user = (
        await db.execute(select(User).where(User.person_id == person_id))
    ).scalar_one_or_none()
    
    if target_user:
        await _guard(db, current_user, target=target_user)
        if _is_admin(target_user) and target_user.is_active and await _active_admin_count(db) <= 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, 
                detail="Cannot delete the last active admin."
            )
    
    await db.delete(person)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Cannot delete person with linked quotes or reservations. Anonymise or reassign records first.",
        )
    return None