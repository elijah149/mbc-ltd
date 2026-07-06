from __future__ import annotations
from typing import Optional
from datetime import date, datetime
import enum

from sqlalchemy import String, ForeignKey, Numeric, Date, DateTime, Enum as SAEnum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class BatchStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    weighed = "weighed"
    approved = "approved"
    rejected = "rejected"


class ProductionBatch(Base, TimestampMixin):
    __tablename__ = "production_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(SAEnum(BatchStatus), default=BatchStatus.pending)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))

    weighing_records: Mapped[list["WeighingRecord"]] = relationship(back_populates="batch")


class WeighingRecord(Base):
    __tablename__ = "weighing_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("production_batches.id"))
    gross_weight: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    net_weight: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    operator_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    batch: Mapped["ProductionBatch"] = relationship(back_populates="weighing_records")


class ProductionLog(Base):
    __tablename__ = "production_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    activity: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    date: Mapped[date] = mapped_column(Date, nullable=False)
