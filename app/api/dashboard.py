"""
Dashboard analytics: totals, statistics, and pending approvals across modules.
"""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.staff import Staff, StaffStatus
from app.models.production import ProductionBatch, BatchStatus
from app.models.inventory import InventoryItem
from app.models.finance import Expense, Revenue, Payment, PaymentStatus
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])


@router.get("/stats")
def overall_stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_employees = db.query(func.count(Staff.id)).filter(Staff.status == StaffStatus.active).scalar()
    pending_payments = db.query(func.count(Payment.id)).filter(
        Payment.status.notin_([PaymentStatus.final_approved, PaymentStatus.rejected])
    ).scalar()
    low_stock_items = db.query(InventoryItem).all()
    low_stock_count = sum(1 for i in low_stock_items if i.is_below_minimum)

    return {
        "total_employees": total_employees,
        "pending_approvals": pending_payments,
        "low_stock_items": low_stock_count,
        "total_production_batches": db.query(func.count(ProductionBatch.id)).scalar(),
    }


@router.get("/finance")
def finance_stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_revenue = db.query(func.coalesce(func.sum(Revenue.amount), 0)).scalar()
    total_expense = db.query(func.coalesce(func.sum(Expense.amount), 0)).scalar()
    return {
        "total_revenue": float(total_revenue),
        "total_expenses": float(total_expense),
        "net_balance": float(total_revenue) - float(total_expense),
        "pending_payments": db.query(func.count(Payment.id)).filter(
            Payment.status.notin_([PaymentStatus.final_approved, PaymentStatus.rejected])
        ).scalar(),
    }


@router.get("/production")
def production_stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    by_status = dict(
        db.query(ProductionBatch.status, func.count(ProductionBatch.id)).group_by(ProductionBatch.status).all()
    )
    return {
        "total_batches": db.query(func.count(ProductionBatch.id)).scalar(),
        "by_status": {str(k): v for k, v in by_status.items()},
    }


@router.get("/inventory")
def inventory_stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    items = db.query(InventoryItem).all()
    return {
        "total_items": len(items),
        "below_minimum": [
            {"id": i.id, "name": i.name, "quantity": float(i.quantity), "minimum_stock": float(i.minimum_stock)}
            for i in items if i.is_below_minimum
        ],
    }
