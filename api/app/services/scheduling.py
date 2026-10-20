from datetime import timedelta

from sqlalchemy import select, text, func, select

from app.models import Reservation
from app.models import Person, Reservation

MAX_MINUTES = 1440


async def lock_schedule(db) -> None:
    """Serialises all booking writes until the transaction ends (fine at clinic scale)."""
    await db.execute(text("SELECT pg_advisory_xact_lock(7001)"))


async def find_conflict(db, start, minutes, patient_id, staff_ids, exclude_id=None):
    end = start + timedelta(minutes=minutes)
    res_end = Reservation.reservation_date + func.make_interval(0, 0, 0, 0, 0, Reservation.duration_minutes)
    where = [
        Reservation.reservation_date >= start - timedelta(minutes=MAX_MINUTES),  # keeps index range
        Reservation.reservation_date < end,
        res_end > start,
    ]
    if exclude_id is not None:
        where.append(Reservation.id != exclude_id)
    if (await db.execute(select(Reservation.id).where(*where, Reservation.patient_id == patient_id).limit(1))).first():
        return "Patient has a scheduling conflict during this time."
    if staff_ids and (await db.execute(
        select(Reservation.id).where(*where, Reservation.staff.any(Person.id.in_(staff_ids))).limit(1)
    )).first():
        return "One or more selected staff members have a scheduling conflict."
    return None