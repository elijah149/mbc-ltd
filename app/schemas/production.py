from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.models.production import BatchStatus


class ProductionBatchCreate(BaseModel):
    batch_number: str
    date: date


class ProductionBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    batch_number: str
    date: date
    status: BatchStatus
    created_by: int


class WeighingRecordCreate(BaseModel):
    batch_id: int
    gross_weight: float
    net_weight: float


class WeighingRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    batch_id: int
    gross_weight: float
    net_weight: float
    operator_id: int
    timestamp: datetime


class ProductionLogCreate(BaseModel):
    employee_id: int
    activity: str
    quantity: Optional[float] = None
    remarks: Optional[str] = None
    date: date


class ProductionLogOut(ProductionLogCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
