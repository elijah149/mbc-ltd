from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict


class InventoryItemCreate(BaseModel):
    name: str
    quantity: float = 0
    unit: Optional[str] = None
    minimum_stock: float = 0
    price: Optional[float] = None


class InventoryItemOut(InventoryItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_below_minimum: bool


class StockInCreate(BaseModel):
    item_id: int
    quantity: float
    supplier: Optional[str] = None
    date: date


class StockInOut(StockInCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recorded_by: Optional[int] = None


class StockOutCreate(BaseModel):
    item_id: int
    quantity: float
    department: Optional[str] = None
    date: date


class StockOutOut(StockOutCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recorded_by: Optional[int] = None
