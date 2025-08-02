from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, DateTime, Float, ForeignKey, Integer, String,
                        Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Faction(Base):
    """
    Represents a faction in the system, which can have users, roles, and offers.
    """

    __tablename__ = "factions"

    faction_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    currency_name: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("currencies.name", ondelete="SET NULL"), nullable=True
    )

    currency_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    roles = relationship(
        "Role",
        back_populates="faction",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    users = relationship("User", back_populates="faction", passive_deletes=True)

    offers = relationship(
        "Offer",
        back_populates="faction",
        foreign_keys="[Offer.faction_id]",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    accepted_offers = relationship(
        "Offer",
        back_populates="accepted_by_faction_obj",
        foreign_keys="[Offer.accepted_by_faction_id]",
    )

    def __repr__(self) -> str:
        return f"<Faction(id={self.faction_id}, name={self.name}, currency={self.currency_name})>"

    def __str__(self) -> str:
        return self.name
