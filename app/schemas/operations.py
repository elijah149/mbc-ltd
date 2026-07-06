from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict

from app.models.operations import OperationStatus


class OperationCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    deadline: Optional[date] = None


class OperationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    status: Optional[OperationStatus] = None
    deadline: Optional[date] = None


class OperationOut(OperationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: OperationStatus
