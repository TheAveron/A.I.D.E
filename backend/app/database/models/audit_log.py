from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..clock import utcnow
from ..database import Base


class AuditLog(Base):
    """Who did what to whom, for actions of staff (admins, train admins).

    Names are copied in: the entry must stay readable after the account or the
    thing it points at is renamed or gone.
    """

    __tablename__ = "admin_audit_log"
    __table_args__ = (Index("ix_audit_created_at", "created_at"),)

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    actor_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    actor_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # An AuditAction value
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    # "user", "faction", "train", "line", "station"
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    detail: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
