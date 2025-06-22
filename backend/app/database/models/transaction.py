from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from ..database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    buyer_faction_id = Column(Integer, ForeignKey("factions.id"), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    offer = relationship("Offer")
    buyer = relationship("User", foreign_keys=[buyer_id])
    buyer_faction = relationship("Faction", foreign_keys=[buyer_faction_id])
    offer = relationship("Offer", back_populates="transactions")

    __table_args__ = (
        CheckConstraint(
            "(buyer_id IS NOT NULL AND buyer_faction_id IS NULL) OR "
            "(buyer_id IS NULL AND buyer_faction_id IS NOT NULL)",
            name="check_one_buyer_type",
        ),
    )

    def __repr__(self):
        return f"<Transaction(id={self.id}, offer_id={self.offer_id}, buyer_id={self.buyer_id}, amount={self.amount}, currency={self.currency}, timestamp={self.timestamp})>"
