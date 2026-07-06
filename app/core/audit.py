"""
Helper to write an AuditLog row. Call this from any endpoint that creates,
updates, approves, or deletes a record so every important action is traceable.
"""
import json
from typing import Any, Optional
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def _serialize(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, default=str)
    except TypeError:
        return str(value)


def log_action(
    db: Session,
    *,
    user_id: Optional[int],
    action: str,
    table_name: Optional[str] = None,
    record_id: Optional[int] = None,
    old_value: Any = None,
    new_value: Any = None,
    commit: bool = True,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_value=_serialize(old_value),
        new_value=_serialize(new_value),
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry
