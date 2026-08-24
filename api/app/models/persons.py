from datetime import date, datetime
from typing import TYPE_CHECKING
from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.reminders import ReminderPreference

if TYPE_CHECKING:
    from app.models.users import User


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    reminder_preference_id: Mapped[int | None] = mapped_column(
        ForeignKey("reminder_preferences.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Eagerly load reminder preference details
    reminder_preference: Mapped[ReminderPreference | None] = relationship(lazy="selectin")

    # 1-to-1 relationship with User account (if this person is a staff member)
    user_account: Mapped["User | None"] = relationship(
        "User",
        back_populates="person",
        uselist=False,
        cascade="all, delete-orphan",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())