from datetime import datetime
from sqlalchemy import Boolean, DateTime, String, func, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Preset(Base):
    __tablename__ = "presets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Store the list of drag-and-drop components and margins as JSON
    elements: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    margins: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())