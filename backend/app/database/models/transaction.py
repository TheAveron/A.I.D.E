from datetime import datetime
from typing import Optional

from sqlalchemy import (CheckConstraint, DateTime, Float, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    offer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("offers.offer_id"), nullable=False, index=True
    )
    offer = relationship(
        "Offer", back_populates="transactions", foreign_keys=[offer_id]
    )

    # Buyer can be either user or faction but not both
    buyer_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True, index=True
    )
    buyer_user = relationship("User", foreign_keys=[buyer_user_id])

    buyer_faction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("factions.faction_id"), nullable=True, index=True
    )
    buyer_faction = relationship("Faction", foreign_keys=[buyer_faction_id])

    # Enforce buyer_user_id XOR buyer_faction_id to be not both null or both set
    __table_args__ = (
        CheckConstraint(
            "(buyer_user_id IS NOT NULL AND buyer_faction_id IS NULL) OR "
            "(buyer_user_id IS NULL AND buyer_faction_id IS NOT NULL)",
            name="check_only_one_buyer",
        ),
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False)

    # Store the currency at the time of transaction for immutability
    currency_name: Mapped[str] = mapped_column(String(50), nullable=False)

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
            f"<Transaction(id={self.transaction_id}, offer_id={self.offer_id}, buyer={buyer}, "
            f"amount={self.amount} {self.currency_name}, timestamp={self.timestamp})>"
        )
