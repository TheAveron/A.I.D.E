from datetime import datetime

from sqlalchemy import (JSON, CheckConstraint, Column, DateTime, Float,
                        ForeignKey, Integer, String)
from sqlalchemy.orm import relationship

from ..database import Base


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="offers")

    faction_id = Column(Integer, ForeignKey("factions.id"), nullable=True)
    faction = relationship("Faction", back_populates="offers")

    item_description = Column(JSON, nullable=False)

    currency = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)

    status = Column(String(20), default="open", nullable=False)

    allowed_parties = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND faction_id IS NULL) OR (user_id IS NULL AND faction_id IS NOT NULL)",
            name="check_only_one_creator",
        ),
    )

    def __repr__(self):
        creator = (
            self.user.username
            if self.user
            else (self.faction.name if self.faction else "Unknown")
        )
        return f"<Offer(creator={creator}, currency={self.currency}, price={self.price}, status={self.status})>"
