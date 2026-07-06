from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.notifications import NotificationType


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    message: str
    type: NotificationType
    read_status: bool
    created_at: datetime


class NotificationCreate(BaseModel):
    user_id: int
    message: str
    type: NotificationType = NotificationType.system
