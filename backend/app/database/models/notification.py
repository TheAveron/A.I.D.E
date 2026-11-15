from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, false
from sqlalchemy.orm import Mapped, mapped_column

from ..clock import utcnow
from ..database import Base


class Notification(Base):
    """Something that happened and concerns one user (shown in their header)."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),
    )

    notification_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    # What kind of event, for the icon / filtering ("join_request", ...)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    # Where in the app the event can be seen, e.g. "/faction/3"
    link: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Notification {self.notification_id} for user {self.user_id}: {self.kind}>"
