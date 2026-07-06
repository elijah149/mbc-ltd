from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.api.deps import require_permission

router = APIRouter(prefix="/audit-logs", tags=["Audit Logging"])


@router.get("")
def list_audit_logs(
    table_name: str | None = None,
    user_id: int | None = None,
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission("view_reports")),
):
    query = db.query(AuditLog)
    if table_name:
        query = query.filter(AuditLog.table_name == table_name)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": l.id, "user_id": l.user_id, "action": l.action,
            "table_name": l.table_name, "record_id": l.record_id,
            "old_value": l.old_value, "new_value": l.new_value,
            "timestamp": l.timestamp,
        }
        for l in logs
    ]
