from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..clock import utcnow
from ..database import Base


class JoinRequest(Base):
    """A user asking to join a faction that only takes members on request."""

    __tablename__ = "join_requests"
    __table_args__ = (
        # One open request per user at a time: no flooding every faction.
        Index(
            "uq_join_requests_one_pending_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'PENDING'"),
            sqlite_where=text("status = 'PENDING'"),
        ),
    )

    request_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False, index=True
    )
    user = relationship("User", foreign_keys=[user_id])

    faction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("factions.faction_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    faction = relationship("Faction", back_populates="join_requests")

    # A JoinRequestStatus value (a plain string keeps the migration simple)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="PENDING")

    message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decided_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True
    )

    @property
    def username(self) -> str:
        return self.user.username

    def __repr__(self) -> str:
        return (
            f"<JoinRequest(id={self.request_id}, user={self.user_id}, "
            f"faction={self.faction_id}, status={self.status})>"
        )
