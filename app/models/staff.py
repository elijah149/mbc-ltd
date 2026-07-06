from __future__ import annotations
from typing import Optional
from datetime import date
import enum

from sqlalchemy import String, ForeignKey, Numeric, Date, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class StaffStatus(str, enum.Enum):
    active = "active"
    on_leave = "on_leave"
    terminated = "terminated"


class Staff(Base, TimestampMixin):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    employee_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(100))
    salary: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    hire_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[StaffStatus] = mapped_column(SAEnum(StaffStatus), default=StaffStatus.active)

    user: Mapped["User"] = relationship(back_populates="staff_profile")
