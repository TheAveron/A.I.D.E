from datetime import datetime
from typing import Optional

from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Index, Integer,
                        Numeric, String)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..clock import utcnow
from ..database import Base


class Transaction(Base):
    """
    Represents a completed transaction resulting from an offer.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "(buyer_user_id IS NOT NULL AND buyer_faction_id IS NULL) OR "
            "(buyer_user_id IS NULL AND buyer_faction_id IS NOT NULL)",
            name="check_only_one_buyer",
        ),
        Index("ix_transactions_offer_id_timestamp", "offer_id", "timestamp"),
    )

    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    offer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("offers.offer_id"), nullable=False, index=True
    )
    offer = relationship(
        "Offer", back_populates="transactions", foreign_keys=[offer_id]
    )

    buyer_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True, index=True
    )
    buyer_user = relationship("User", foreign_keys=[buyer_user_id])

    buyer_faction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("factions.faction_id"), nullable=True, index=True
    )
    buyer_faction = relationship("Faction", foreign_keys=[buyer_faction_id])

    amount: Mapped[float] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False
    )

    currency_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("currencies.currency_id"), nullable=False, index=True
    )
    currency = relationship("Currency")

    @property
    def currency_name(self) -> Optional[str]:
        """The currency's current name (it may have been renamed since)."""
        return self.currency.name if self.currency else None

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    # How many units were bought (empty for the oldest rows, which only kept
    # the amount)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # An admin can cancel a transaction; the row stays as the record of it
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, index=True
    )
    cancelled_by_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    def __repr__(self) -> str:
        buyer = (
            self.buyer_user.username
            if self.buyer_user
            else (self.buyer_faction.name if self.buyer_faction else "Unknown")
        )
        return (
            f"<Transaction(id={self.transaction_id}, offer_id={self.offer_id}, "
            f"buyer={buyer}, amount={self.amount} {self.currency_name}, "
            f"timestamp={self.timestamp})>"
        )
