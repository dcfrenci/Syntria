from datetime import timedelta
from sqlalchemy import select, text

from app.models import Reservation

MAX_MINUTES = 1440


async def lock_schedule(db) -> None:
    """Serialises all booking writes until the transaction ends (fine at clinic scale)."""
    await db.execute(text("SELECT pg_advisory_xact_lock(7001)"))


async def find_conflict(db, start, minutes, patient_id, staff_ids, exclude_id=None) -> str | None:
    end = start + timedelta(minutes=minutes)
    q = select(Reservation).where(
        Reservation.reservation_date >= start - timedelta(minutes=MAX_MINUTES),
        Reservation.reservation_date < end,
    )
    if exclude_id is not None:
        q = q.where(Reservation.id != exclude_id)
    wanted = set(staff_ids)
    for res in (await db.execute(q)).scalars().unique():
        if res.reservation_date + timedelta(minutes=res.duration_minutes) <= start:
            continue
        if res.patient_id == patient_id:
            return "Patient has a scheduling conflict during this time."
        if wanted & {s.id for s in res.staff}:
            return "One or more selected staff members have a scheduling conflict."
    return None