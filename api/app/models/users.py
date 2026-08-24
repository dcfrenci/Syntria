from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.persons import Person
    from app.models.roles import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Foreign Keys
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("persons.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="selectin")
    person: Mapped["Person"] = relationship("Person", back_populates="user_account", lazy="selectin")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())