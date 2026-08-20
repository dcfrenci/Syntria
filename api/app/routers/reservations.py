from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.persons import Person
from app.models.reservations import Reservation
from app.schemas.reservations import (
    ReservationCreate,
    ReservationListResponse,
    ReservationResponse,
    ReservationUpdate,
)

router = APIRouter(prefix="/reservations", tags=["Reservations"])

@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    payload: ReservationCreate,
    db: AsyncSession = Depends(get_db),
):
    # 1. Calculate time windows for overlap checking
    start_time = payload.reservation_date
    end_time = start_time + timedelta(minutes=payload.duration_minutes)
    
    # Narrow DB search window to +/- 12 hours for performance
    window_start = start_time - timedelta(hours=12)
    window_end = start_time + timedelta(hours=12)

    # 2. Verify patient exists
    patient = await db.get(Person, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    # 3. Check Patient double-booking
    patient_reservations = (await db.execute(
        select(Reservation).where(
            Reservation.patient_id == payload.patient_id,
            Reservation.reservation_date >= window_start,
            Reservation.reservation_date <= window_end
        )
    )).scalars().all()

    for res in patient_reservations:
        res_end = res.reservation_date + timedelta(minutes=res.duration_minutes)
        if start_time < res_end and end_time > res.reservation_date:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient has a scheduling conflict during this time.")

    # 4. Verify staff exist and check Staff double-booking
    staff_members = (await db.execute(select(Person).where(Person.id.in_(payload.staff_ids)))).scalars().all()
    if len(staff_members) != len(set(payload.staff_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more staff IDs are invalid.")

    staff_reservations = (await db.execute(
        select(Reservation)
        .join(Reservation.staff)
        .where(
            Person.id.in_(payload.staff_ids),
            Reservation.reservation_date >= window_start,
            Reservation.reservation_date <= window_end
        )
    )).scalars().all()

    for res in staff_reservations:
        res_end = res.reservation_date + timedelta(minutes=res.duration_minutes)
        if start_time < res_end and end_time > res.reservation_date:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="One or more selected staff members have a scheduling conflict.")

    # 5. Create Reservation
    reservation = Reservation(
        patient_id=payload.patient_id,
        reservation_date=payload.reservation_date,
        duration_minutes=payload.duration_minutes,
        description=payload.description,
    )
    reservation.staff.extend(staff_members)

    db.add(reservation)
    await db.flush()
    await db.refresh(reservation)
    return reservation


@router.patch("/{reservation_id}", response_model=ReservationResponse, status_code=status.HTTP_200_OK)
async def update_reservation(
    reservation_id: int,
    payload: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
):
    reservation = await db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found.")

    update_data = payload.model_dump(exclude_unset=True)
    
    # Calculate proposed new values (falling back to current values if not updated)
    target_date = update_data.get("reservation_date", reservation.reservation_date)
    target_duration = update_data.get("duration_minutes", reservation.duration_minutes)
    target_patient_id = update_data.get("patient_id", reservation.patient_id)
    target_staff_ids = update_data.get("staff_ids", [s.id for s in reservation.staff])

    start_time = target_date
    end_time = start_time + timedelta(minutes=target_duration)
    window_start = start_time - timedelta(hours=12)
    window_end = start_time + timedelta(hours=12)

    # 1. Check Patient double-booking
    if "reservation_date" in update_data or "duration_minutes" in update_data or "patient_id" in update_data:
        patient_reservations = (await db.execute(
            select(Reservation).where(
                Reservation.id != reservation_id,
                Reservation.patient_id == target_patient_id,
                Reservation.reservation_date >= window_start,
                Reservation.reservation_date <= window_end
            )
        )).scalars().all()

        for res in patient_reservations:
            res_end = res.reservation_date + timedelta(minutes=res.duration_minutes)
            if start_time < res_end and end_time > res.reservation_date:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient has a scheduling conflict during this time.")

    # 2. Check Staff double-booking & fetch updated staff list
    if "reservation_date" in update_data or "duration_minutes" in update_data or "staff_ids" in update_data:
        staff_members = (await db.execute(select(Person).where(Person.id.in_(target_staff_ids)))).scalars().all()
        if len(staff_members) != len(set(target_staff_ids)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more staff IDs are invalid.")

        staff_reservations = (await db.execute(
            select(Reservation)
            .join(Reservation.staff)
            .where(
                Reservation.id != reservation_id,
                Person.id.in_(target_staff_ids),
                Reservation.reservation_date >= window_start,
                Reservation.reservation_date <= window_end
            )
        )).scalars().all()

        for res in staff_reservations:
            res_end = res.reservation_date + timedelta(minutes=res.duration_minutes)
            if start_time < res_end and end_time > res.reservation_date:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="One or more selected staff members have a scheduling conflict.")
        
        if "staff_ids" in update_data:
            reservation.staff.clear()
            reservation.staff.extend(staff_members)

    # 3. Apply standard scalar updates
    if "description" in update_data:
        reservation.description = update_data["description"]
    if "reservation_date" in update_data:
        reservation.reservation_date = update_data["reservation_date"]
    if "duration_minutes" in update_data:
        reservation.duration_minutes = update_data["duration_minutes"]
    if "patient_id" in update_data:
        reservation.patient_id = update_data["patient_id"]

    await db.flush()
    await db.refresh(reservation)
    return reservation


@router.get("/", response_model=ReservationListResponse, status_code=status.HTTP_200_OK)
async def get_reservations(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    query = select(Reservation).order_by(Reservation.reservation_date.desc())
    count_query = select(func.count(Reservation.id))

    total = (await db.execute(count_query)).scalar_one()
    reservations = (await db.execute(query.offset(skip).limit(limit))).scalars().all()

    return {"total": total, "reservations": reservations}


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(reservation_id: int, db: AsyncSession = Depends(get_db)):
    reservation = await db.get(Reservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found.")

    await db.delete(reservation)
    return None