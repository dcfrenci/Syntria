from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.persons import Person

# Many-to-Many association table
reservation_staff_m2m = Table(
    "reservation_staff",
    Base.metadata,
    Column("reservation_id", ForeignKey("reservations.id", ondelete="CASCADE"), primary_key=True),
    Column("person_id", ForeignKey("persons.id", ondelete="CASCADE"), primary_key=True),
)

class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"), index=True)
    reservation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    patient: Mapped["Person"] = relationship("Person", foreign_keys=[patient_id], lazy="selectin")
    staff: Mapped[list["Person"]] = relationship("Person", secondary=reservation_staff_m2m, lazy="selectin")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())