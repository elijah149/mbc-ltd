from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.user import UserStatus


class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentOut(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    level: int = 99
    reports_to_role_id: Optional[int] = None


class RoleCreate(RoleBase):
    permission_ids: list[int] = []


class RoleOut(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class UserBase(BaseModel):
    fullname: str
    email: EmailStr
    phone: Optional[str] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    role_id: Optional[int] = None
    status: Optional[UserStatus] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: UserStatus
    is_superuser: bool
    department: Optional[DepartmentOut] = None
    role: Optional[RoleOut] = None
