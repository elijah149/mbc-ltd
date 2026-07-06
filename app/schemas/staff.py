from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict

from app.models.staff import StaffStatus


class StaffBase(BaseModel):
    user_id: int
    employee_number: str
    position: Optional[str] = None
    salary: Optional[float] = None
    hire_date: Optional[date] = None


class StaffCreate(StaffBase):
    pass


class StaffUpdate(BaseModel):
    position: Optional[str] = None
    salary: Optional[float] = None
    status: Optional[StaffStatus] = None


class StaffOut(StaffBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: StaffStatus
