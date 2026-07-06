"""
User, Role, Permission, Department management endpoints.
Requires 'manage_users' permission for mutation endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.core.audit import log_action
from app.models.user import User, Role, Permission, RolePermission, Department
from app.schemas.user import (
    UserCreate, UserUpdate, UserOut,
    RoleCreate, RoleOut, PermissionOut,
    DepartmentCreate, DepartmentOut,
)
from app.api.deps import get_current_user, require_permission

router = APIRouter(tags=["Users & RBAC"])


# --------------------------------------------------------------------- Users
@router.get("/users", response_model=list[UserOut])
def list_users(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("manage_users")),
):
    return db.query(User).offset(skip).limit(limit).all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("create_staff")),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        fullname=payload.fullname,
        email=payload.email,
        phone=payload.phone,
        department_id=payload.department_id,
        role_id=payload.role_id,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_action(db, user_id=current_user.id, action="User created", table_name="users", record_id=user.id, new_value=payload.model_dump(exclude={"password"}))
    return user


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int, payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_value = {"fullname": user.fullname, "phone": user.phone, "status": user.status}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)

    log_action(db, user_id=current_user.id, action="User updated", table_name="users", record_id=user.id, old_value=old_value, new_value=payload.model_dump(exclude_unset=True))
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("delete_staff")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    log_action(db, user_id=current_user.id, action="User deleted", table_name="users", record_id=user_id)


# --------------------------------------------------------------- Departments
@router.get("/departments", response_model=list[DepartmentOut])
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Department).all()


@router.post("/departments", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    dept = Department(**payload.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    log_action(db, user_id=current_user.id, action="Department created", table_name="departments", record_id=dept.id, new_value=payload.model_dump())
    return dept


# --------------------------------------------------------------------- Roles
@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Role).all()


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("manage_users")),
):
    role = Role(
        name=payload.name,
        description=payload.description,
        level=payload.level,
        reports_to_role_id=payload.reports_to_role_id,
    )
    db.add(role)
    db.flush()

    for perm_id in payload.permission_ids:
        db.add(RolePermission(role_id=role.id, permission_id=perm_id))

    db.commit()
    db.refresh(role)
    log_action(db, user_id=current_user.id, action="Role created", table_name="roles", record_id=role.id, new_value=payload.model_dump())
    return role


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Permission).all()
