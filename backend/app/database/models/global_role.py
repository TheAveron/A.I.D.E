from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..clock import utcnow
from ..database import Base


class GlobalRoleName(str, Enum):
    """The server-wide roles that exist."""

    ADMIN = "admin"  # everything an admin may do (approve factions, ...)
    TRAIN_ADMIN = "train_admin"  # manages every train, line and station


class GlobalRole(Base):
    """A server-wide role held by a user, outside any faction.

    One row per (user, role): "admin", "train_admin", and whatever comes next
    (moderators...). Keeping them here, rather than as columns of `users`,
    means a new role is a new value, not a migration.
    """

    __tablename__ = "user_global_roles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    # A GlobalRoleName value (a plain string keeps new roles migration-free)
    role: Mapped[str] = mapped_column(String(30), primary_key=True)

    granted_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    user = relationship("User", back_populates="global_roles")

    def __repr__(self) -> str:
        return f"<GlobalRole(user={self.user_id}, role={self.role})>"
