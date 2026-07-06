"""
Helper to create in-app notifications. Email dispatch is delegated to a
Celery task (see app/core/celery_app.py) so the request path stays fast.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.notifications import Notification, NotificationType


def notify_user(
    db: Session,
    *,
    user_id: int,
    message: str,
    type: NotificationType = NotificationType.system,
    commit: bool = True,
) -> Notification:
    notification = Notification(user_id=user_id, message=message, type=type)
    db.add(notification)
    if commit:
        db.commit()
        db.refresh(notification)
    return notification
