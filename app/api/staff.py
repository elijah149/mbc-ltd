from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.models.user import User
from app.models.staff import Staff
from app.schemas.staff import StaffCreate, StaffUpdate, StaffOut
from app.api.deps import get_current_user, require_permission

router = APIRouter(prefix="/staff", tags=["Staff Management"])


@router.get("", response_model=list[StaffOut])
def list_staff(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Staff).offset(skip).limit(limit).all()


@router.post("", response_model=StaffOut, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("create_staff")),
):
    if db.query(Staff).filter(Staff.employee_number == payload.employee_number).first():
        raise HTTPException(status_code=400, detail="Employee number already exists")
    staff = Staff(**payload.model_dump())
    db.add(staff)
    db.commit()
    db.refresh(staff)
    log_action(db, user_id=current_user.id, action="Staff created", table_name="staff", record_id=staff.id, new_value=payload.model_dump())
    return staff


@router.put("/{staff_id}", response_model=StaffOut)
def update_staff(
    staff_id: int, payload: StaffUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("create_staff")),
):
    staff = db.get(Staff, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    old_value = {"position": staff.position, "salary": float(staff.salary) if staff.salary else None, "status": staff.status}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(staff, field, value)
    db.commit()
    db.refresh(staff)
    log_action(db, user_id=current_user.id, action="Staff updated", table_name="staff", record_id=staff.id, old_value=old_value, new_value=payload.model_dump(exclude_unset=True))
    return staff


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    staff_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("delete_staff")),
):
    staff = db.get(Staff, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    db.delete(staff)
    db.commit()
    log_action(db, user_id=current_user.id, action="Staff deleted", table_name="staff", record_id=staff_id)
