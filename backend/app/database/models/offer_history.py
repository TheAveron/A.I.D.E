import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base


class OfferAction(enum.Enum):
    """Possible actions recorded in the offer history."""

    CREATED = "created"
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"


class OfferHistory(Base):
    """
    Represents a log entry of an action taken on an offer.
    """

    __tablename__ = "offer_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    offer_id: Mapped[int] = mapped_column(
        ForeignKey("offers.offer_id"),
        nullable=False,
    )

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.user_id"), nullable=True
    )

    action: Mapped[OfferAction] = mapped_column(Enum(OfferAction), nullable=False)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    offer = relationship("Offer", back_populates="history")

    user = relationship("User")

    def __repr__(self) -> str:
        return f"<OfferHistory(offer_id={self.offer_id}, action={self.action.value}, timestamp={self.timestamp})>"

    def __str__(self) -> str:
        return f"Offer {self.offer_id} - {self.action.value} at {self.timestamp}"
