"""
Core identity & RBAC models: User, Role, Permission, Department,
plus the many-to-many RolePermission link and LoginHistory audit table.

Organizational hierarchy encoded via `role.level` and `department`:

    Board of Directors (Body Manager)
            -> Manager
                -> Production Manager -> Weighing Officer, Industry Employee
                -> Store Keeper
                -> Accountant Manager -> Accountant Officer -> Accounts Clerk
                -> Operation Manager -> Operation Officer
                -> IT Officer
"""
from __future__ import annotations
from typing import Optional, List
import enum

from sqlalchemy import String, Boolean, ForeignKey, Enum as SAEnum, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    suspended = "suspended"


# ---------------------------------------------------------------- Department
class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    users: Mapped[List["User"]] = relationship(back_populates="department")


# --------------------------------------------------------------- Permission
class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    role_links: Mapped[List["RolePermission"]] = relationship(back_populates="permission")


# --------------------------------------------------------------------- Role
class Role(Base, TimestampMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    # hierarchy level: 0 = Board/Body Manager (highest) ... higher number = lower rank
    level: Mapped[int] = mapped_column(Integer, default=99)
    # role this one reports to, used for approval-chain escalation
    reports_to_role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"), nullable=True)

    reports_to: Mapped[Optional["Role"]] = relationship(remote_side="Role.id")
    permission_links: Mapped[List["RolePermission"]] = relationship(back_populates="role")
    users: Mapped[List["User"]] = relationship(back_populates="role")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), primary_key=True)

    role: Mapped["Role"] = relationship(back_populates="permission_links")
    permission: Mapped["Permission"] = relationship(back_populates="role_links")


# --------------------------------------------------------------------- User
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    fullname: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"))

    status: Mapped[UserStatus] = mapped_column(SAEnum(UserStatus), default=UserStatus.active)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    department: Mapped[Optional["Department"]] = relationship(back_populates="users")
    role: Mapped[Optional["Role"]] = relationship(back_populates="users")
    staff_profile: Mapped[Optional["Staff"]] = relationship(back_populates="user", uselist=False)

    def has_permission(self, permission_name: str) -> bool:
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return any(link.permission.name == permission_name for link in self.role.permission_links)


class LoginHistory(Base):
    __tablename__ = "login_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
