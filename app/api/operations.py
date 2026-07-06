from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.core.notify import notify_user
from app.models.user import User
from app.models.operations import Operation
from app.schemas.operations import OperationCreate, OperationUpdate, OperationOut
from app.api.deps import get_current_user, require_role

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.get("", response_model=list[OperationOut])
def list_operations(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Operation).all()


@router.post("", response_model=OperationOut, status_code=status.HTTP_201_CREATED)
def create_operation(
    payload: OperationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Operation Manager", "Manager")),
):
    operation = Operation(**payload.model_dump())
    db.add(operation)
    db.commit()
    db.refresh(operation)
    log_action(db, user_id=current_user.id, action="Operation created", table_name="operations", record_id=operation.id, new_value=payload.model_dump())
    if operation.assigned_to:
        notify_user(db, user_id=operation.assigned_to, message=f"You have been assigned a new operation: {operation.title}")
    return operation


@router.put("/{operation_id}", response_model=OperationOut)
def update_operation(
    operation_id: int, payload: OperationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Operation Manager", "Operation Officer", "Manager")),
):
    operation = db.get(Operation, operation_id)
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    old_value = {"status": operation.status, "title": operation.title}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(operation, field, value)
    db.commit()
    db.refresh(operation)
    log_action(db, user_id=current_user.id, action="Operation updated", table_name="operations", record_id=operation.id, old_value=old_value, new_value=payload.model_dump(exclude_unset=True))
    return operation


@router.delete("/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operation(
    operation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Operation Manager", "Manager")),
):
    operation = db.get(Operation, operation_id)
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    db.delete(operation)
    db.commit()
    log_action(db, user_id=current_user.id, action="Operation deleted", table_name="operations", record_id=operation_id)
