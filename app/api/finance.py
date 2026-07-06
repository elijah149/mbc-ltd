"""
Finance module, managed by Accountant Manager, Accountant Officer, Accounts Clerk.

Financial approval chain:
    Accounts Clerk -> Accountant Officer -> Accountant Manager -> Manager -> Approved
Each POST /approve-payment call advances the payment exactly one step, and only
a user holding the *next* role in the chain (or higher) may advance it.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.core.notify import notify_user
from app.models.user import User, Role
from app.models.finance import Account, Expense, Revenue, Payment, PaymentStatus
from app.schemas.finance import (
    AccountCreate, AccountOut,
    ExpenseCreate, ExpenseOut,
    RevenueCreate, RevenueOut,
    PaymentCreate, PaymentOut, PaymentApprove,
)
from app.api.deps import get_current_user, require_permission, require_role

router = APIRouter(tags=["Finance"])

# ordered approval chain: role required to move payment FROM this status
_APPROVAL_CHAIN: list[tuple[PaymentStatus, str, PaymentStatus]] = [
    (PaymentStatus.pending, "Accounts Clerk", PaymentStatus.clerk_reviewed),
    (PaymentStatus.clerk_reviewed, "Accountant Officer", PaymentStatus.officer_reviewed),
    (PaymentStatus.officer_reviewed, "Accountant Manager", PaymentStatus.manager_approved),
    (PaymentStatus.manager_approved, "Manager", PaymentStatus.final_approved),
]


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db), _: User = Depends(require_permission("manage_finance"))):
    return db.query(Account).all()


@router.post("/accounts", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_finance")),
):
    account = Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    log_action(db, user_id=current_user.id, action="Account created", table_name="accounts", record_id=account.id, new_value=payload.model_dump())
    return account


# ------------------------------------------------------------------ Expenses
@router.get("/expenses", response_model=list[ExpenseOut])
def list_expenses(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Expense).all()


@router.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_finance")),
):
    expense = Expense(**payload.model_dump(), created_by=current_user.id)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    log_action(db, user_id=current_user.id, action="Expense recorded", table_name="expenses", record_id=expense.id, new_value=payload.model_dump())
    return expense


# ------------------------------------------------------------------ Revenues
@router.get("/revenues", response_model=list[RevenueOut])
def list_revenues(db: Session = Depends(get_db), _: User = Depends(require_permission("manage_finance"))):
    return db.query(Revenue).all()


@router.post("/revenues", response_model=RevenueOut, status_code=status.HTTP_201_CREATED)
def create_revenue(
    payload: RevenueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_finance")),
):
    revenue = Revenue(**payload.model_dump())
    db.add(revenue)
    db.commit()
    db.refresh(revenue)
    log_action(db, user_id=current_user.id, action="Revenue recorded", table_name="revenues", record_id=revenue.id, new_value=payload.model_dump())
    return revenue


# ------------------------------------------------------------------ Payments
@router.get("/payments", response_model=list[PaymentOut])
def list_payments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Payment).all()


@router.post("/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Accounts Clerk", "Accountant Officer", "Accountant Manager", "Manager")),
):
    payment = Payment(**payload.model_dump(), created_by=current_user.id)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    log_action(db, user_id=current_user.id, action="Payment requested", table_name="payments", record_id=payment.id, new_value=payload.model_dump())
    return payment


@router.post("/approve-payment/{payment_id}", response_model=PaymentOut)
def approve_payment(
    payment_id: int,
    payload: PaymentApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    step = next((s for s in _APPROVAL_CHAIN if s[0] == payment.status), None)
    if step is None:
        raise HTTPException(status_code=400, detail=f"Payment is already at a terminal state: {payment.status}")

    _, required_role, next_status = step
    if not current_user.is_superuser and (not current_user.role or current_user.role.name != required_role):
        raise HTTPException(status_code=403, detail=f"Only {required_role} can act on this payment at its current stage")

    old_status = payment.status
    if not payload.approve:
        payment.status = PaymentStatus.rejected
    else:
        payment.status = next_status
        if next_status == PaymentStatus.final_approved:
            payment.approved_by = current_user.id

    db.commit()
    db.refresh(payment)

    log_action(db, user_id=current_user.id, action=f"Payment {'approved' if payload.approve else 'rejected'} at {required_role} stage",
               table_name="payments", record_id=payment.id, old_value=old_status.value, new_value=payment.status.value)

    notify_user(db, user_id=payment.created_by, message=f"Payment #{payment.id} status changed: {old_status.value} -> {payment.status.value}")

    return payment
