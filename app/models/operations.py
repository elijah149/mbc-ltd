from __future__ import annotations
from typing import Optional
from datetime import date
import enum

from sqlalchemy import String, ForeignKey, Date, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class OperationStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Operation(Base, TimestampMixin):
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    assigned_to: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    status: Mapped[OperationStatus] = mapped_column(SAEnum(OperationStatus), default=OperationStatus.pending)
    deadline: Mapped[Optional[date]] = mapped_column(Date)
