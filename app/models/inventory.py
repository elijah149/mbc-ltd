from __future__ import annotations
from typing import Optional
from datetime import date

from sqlalchemy import String, ForeignKey, Numeric, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    unit: Mapped[Optional[str]] = mapped_column(String(30))
    minimum_stock: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    stock_ins: Mapped[list["StockIn"]] = relationship(back_populates="item")
    stock_outs: Mapped[list["StockOut"]] = relationship(back_populates="item")

    @property
    def is_below_minimum(self) -> bool:
        return self.quantity < self.minimum_stock


class StockIn(Base):
    __tablename__ = "stock_in"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    supplier: Mapped[Optional[str]] = mapped_column(String(150))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    recorded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    item: Mapped["InventoryItem"] = relationship(back_populates="stock_ins")


class StockOut(Base):
    __tablename__ = "stock_out"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(100))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    recorded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    item: Mapped["InventoryItem"] = relationship(back_populates="stock_outs")
