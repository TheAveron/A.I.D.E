from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

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

    currency_name: Mapped[str] = mapped_column(
        String(50), ForeignKey("currencies.name"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

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
