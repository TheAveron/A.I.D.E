from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (JSON, CheckConstraint, Column, DateTime, Enum, Float,
                        ForeignKey, Integer, String)
from sqlalchemy.orm import relationship

from ..database import Base


class OfferType(PyEnum):
    BUY = "buy"
    SELL = "sell"


class OfferStatus(PyEnum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)

    # Creator (either user or faction)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="offers")

    faction_id = Column(Integer, ForeignKey("factions.id"), nullable=True)
    faction = relationship("Faction", back_populates="offers")

    # What is being offered/requested
    offer_type = Column(Enum(OfferType), nullable=False)
    item_description = Column(JSON, nullable=False)

    # Price
    currency = Column(String(50), nullable=False)  # Custom currency name
    price_per_unit = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

    # Optional restrictions
    allowed_parties = Column(JSON, nullable=True)  # List of user/faction IDs

    # State & metadata
    status = Column(Enum(OfferStatus), default=OfferStatus.OPEN, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND faction_id IS NULL) OR "
            "(user_id IS NULL AND faction_id IS NOT NULL)",
            name="check_only_one_creator",
        ),
    )

    def __repr__(self):
        creator = (
            self.user.username
            if self.user
            else (self.faction.name if self.faction else "Unknown")
        )
        return (
            f"<Offer(id={self.id}, creator={creator}, type={self.offer_type}, "
            f"item={self.item_description}, price={self.price_per_unit}, "
            f"quantity={self.quantity}, status={self.status})>"
        )
