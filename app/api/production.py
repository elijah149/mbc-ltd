"""
Production module.

Approval workflow (see approvals.py for the generic escalation helper):
    Industry Employee -> Weighing Officer -> Production Manager -> Manager
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.core.notify import notify_user
from app.models.user import User
from app.models.production import ProductionBatch, WeighingRecord, ProductionLog, BatchStatus
from app.schemas.production import (
    ProductionBatchCreate, ProductionBatchOut,
    WeighingRecordCreate, WeighingRecordOut,
    ProductionLogCreate, ProductionLogOut,
)
from app.api.deps import get_current_user, require_permission, require_role

router = APIRouter(prefix="/production", tags=["Production"])


# -------------------------------------------------------------------- Batch
@router.get("/batches", response_model=list[ProductionBatchOut])
def list_batches(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ProductionBatch).all()


@router.post("/batches", response_model=ProductionBatchOut, status_code=status.HTTP_201_CREATED)
def create_batch(
    payload: ProductionBatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_production")),
):
    if db.query(ProductionBatch).filter(ProductionBatch.batch_number == payload.batch_number).first():
        raise HTTPException(status_code=400, detail="Batch number already exists")
    batch = ProductionBatch(**payload.model_dump(), created_by=current_user.id)
    db.add(batch)
    db.commit()
    db.refresh(batch)
    log_action(db, user_id=current_user.id, action="Production batch created", table_name="production_batches", record_id=batch.id, new_value=payload.model_dump())
    return batch


@router.get("", response_model=list[ProductionBatchOut])
def production_overview(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """GET /production - general production overview (alias of batches list)."""
    return db.query(ProductionBatch).all()


# ---------------------------------------------------------------- Weighing
# Registered without the /production prefix to match spec: POST /weighing
weighing_router = APIRouter(tags=["Production"])


@weighing_router.post("/weighing", response_model=WeighingRecordOut, status_code=status.HTTP_201_CREATED)
def record_weighing(
    payload: WeighingRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Weighing Officer", "Production Manager", "Manager")),
):
    batch = db.get(ProductionBatch, payload.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    record = WeighingRecord(**payload.model_dump(), operator_id=current_user.id)
    db.add(record)
    batch.status = BatchStatus.weighed
    db.commit()
    db.refresh(record)

    log_action(db, user_id=current_user.id, action="Weighing recorded", table_name="weighing_records", record_id=record.id, new_value=payload.model_dump())

    if batch.created_by:
        notify_user(db, user_id=batch.created_by, message=f"Batch {batch.batch_number} has been weighed: net {payload.net_weight}")

    return record



# ------------------------------------------------------------- Production log
@router.get("/logs", response_model=list[ProductionLogOut])
def list_logs(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(ProductionLog).all()


@router.post("/logs", response_model=ProductionLogOut, status_code=status.HTTP_201_CREATED)
def create_log(
    payload: ProductionLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Industry Employee", "Weighing Officer", "Production Manager", "Manager")),
):
    log_entry = ProductionLog(**payload.model_dump())
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    log_action(db, user_id=current_user.id, action="Production log added", table_name="production_logs", record_id=log_entry.id, new_value=payload.model_dump())
    return log_entry


@router.post("/batches/{batch_id}/approve", response_model=ProductionBatchOut)
def approve_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Production Manager", "Manager")),
):
    batch = db.get(ProductionBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    old_status = batch.status
    batch.status = BatchStatus.approved
    db.commit()
    db.refresh(batch)
    log_action(db, user_id=current_user.id, action="Production batch approved", table_name="production_batches", record_id=batch.id, old_value=old_status.value, new_value=batch.status.value)
    return batch
