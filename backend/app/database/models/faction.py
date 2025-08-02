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

    faction_id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optional currency reference (name of the currency the faction uses)
    currency_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    currency_amount: Mapped[float] = mapped_column(Float, default=0.0)

    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    roles = relationship("Role", back_populates="faction", cascade="all, delete-orphan")

    users = relationship("User", back_populates="faction")

    offers = relationship(
        "Offer",
        back_populates="faction",
        foreign_keys="[Offer.faction_id]",  # creation FK
        cascade="all, delete-orphan",
    )

    accepted_offers = relationship(
        "Offer",
        back_populates="accepted_by_faction_obj",
        foreign_keys="[Offer.accepted_by_faction_id]",  # acceptance FK
    )

    def __repr__(self) -> str:
        return f"<Faction(name={self.name}, currency={self.currency_name})>"

    def __str__(self) -> str:
        return f"Faction: {self.name}"
