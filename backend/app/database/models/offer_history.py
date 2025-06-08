import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class OfferAction(enum.Enum):
    CREATED = "created"
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"


class OfferHistory(Base):
    __tablename__ = "offer_history"

    id = Column(Integer, primary_key=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(Enum(OfferAction), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)

    offer = relationship("Offer", back_populates="history")
    user = relationship("User")
