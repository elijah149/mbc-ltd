from typing import Optional
from datetime import date
from pydantic import BaseModel, ConfigDict

from app.models.finance import AccountType, PaymentStatus


class AccountCreate(BaseModel):
    name: str
    type: AccountType
    balance: float = 0


class AccountOut(AccountCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ExpenseCreate(BaseModel):
    category: str
    amount: float
    description: Optional[str] = None
    date: date


class ExpenseOut(ExpenseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_by: int


class RevenueCreate(BaseModel):
    source: str
    amount: float
    date: date


class RevenueOut(RevenueCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PaymentCreate(BaseModel):
    amount: float
    description: Optional[str] = None


class PaymentOut(PaymentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: PaymentStatus
    created_by: int
    approved_by: Optional[int] = None


class PaymentApprove(BaseModel):
    approve: bool
    remarks: Optional[str] = None
