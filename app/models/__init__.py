"""
Import every model here so that:
  1. Alembic's autogenerate can discover all tables via Base.metadata
  2. SQLAlchemy can resolve string-based relationship() references between modules
"""
from app.models.user import User, Role, Permission, RolePermission, Department, LoginHistory, UserStatus
from app.models.staff import Staff, StaffStatus
from app.models.production import ProductionBatch, WeighingRecord, ProductionLog, BatchStatus
from app.models.inventory import InventoryItem, StockIn, StockOut
from app.models.finance import Account, Expense, Revenue, Payment, AccountType, PaymentStatus
from app.models.operations import Operation, OperationStatus
from app.models.documents import Document
from app.models.notifications import Notification, NotificationType
from app.models.audit import AuditLog

__all__ = [
    "User", "Role", "Permission", "RolePermission", "Department", "LoginHistory", "UserStatus",
    "Staff", "StaffStatus",
    "ProductionBatch", "WeighingRecord", "ProductionLog", "BatchStatus",
    "InventoryItem", "StockIn", "StockOut",
    "Account", "Expense", "Revenue", "Payment", "AccountType", "PaymentStatus",
    "Operation", "OperationStatus",
    "Document",
    "Notification", "NotificationType",
    "AuditLog",
]
