from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.orm import relationship

from ..database import Base


class Faction(Base):
    __tablename__ = "factions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    currency_name = Column(String(50), nullable=True)
    currency_amount = Column(Float, default=0.0)

    is_approved = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship("Role", back_populates="faction", cascade="all, delete-orphan")
    users = relationship("User", back_populates="faction")
    offers = relationship("Offer", back_populates="faction")

    def __repr__(self):
        return f"<Faction(name={self.name}, currency={self.currency_name})>"
