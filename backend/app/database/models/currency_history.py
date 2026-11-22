from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..clock import utcnow
from ..database import Base


class CurrencyHistory(Base):
    """
    Log entry recording a change to a currency's `total_in_circulation`.

    `total_in_circulation` is a self-reported figure (there is no
    per-user/per-faction balance ledger in this system - the actual
    currency being tracked exists as physical items in the game world,
    not as balances this app can compute). This table doesn't try to
    derive that figure automatically; it only adds accountability for
    who changed the declared figure, when, and from/to what value.

    A rename is logged here as well (with the total unchanged and the old
    and new names in `notes`), so the trail stays readable afterwards.
    """

    __tablename__ = "currency_history"
    __table_args__ = (
        Index(
            "ix_currency_history_currency_id_timestamp",
            "currency_id",
            "timestamp",
        ),
    )

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    currency_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("currencies.currency_id"), nullable=False, index=True
    )
    currency = relationship(
        "Currency", back_populates="history", foreign_keys=[currency_id]
    )

    @property
    def currency_name(self) -> Optional[str]:
        """The currency's current name (it may have been renamed since)."""
        return self.currency.name if self.currency else None

    actor_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True, index=True
    )
    actor_user = relationship("User", foreign_keys=[actor_user_id])

    old_total_in_circulation: Mapped[int] = mapped_column(Integer, nullable=False)
    new_total_in_circulation: Mapped[int] = mapped_column(Integer, nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        actor = self.actor_user.username if self.actor_user else "Unknown"
        return (
            f"<CurrencyHistory(id={self.history_id}, currency={self.currency_name}, "
            f"actor={actor}, {self.old_total_in_circulation} -> "
            f"{self.new_total_in_circulation}, timestamp={self.timestamp})>"
        )

    def __str__(self) -> str:
        return (
            f"{self.currency_name}: {self.old_total_in_circulation} -> "
            f"{self.new_total_in_circulation} at {self.timestamp}"
        )
