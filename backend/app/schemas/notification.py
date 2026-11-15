from typing import Optional

from pydantic import BaseModel, ConfigDict

from .base import UTCDatetime


class NotificationOut(BaseModel):
    notification_id: int
    kind: str
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCount(BaseModel):
    count: int
