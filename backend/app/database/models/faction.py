from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text
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

    currency = relationship(
        "Currency",
        back_populates="faction",
        foreign_keys="[Currency.faction_id]",  # <-- Explicitly specify foreign key
        uselist=False,
        cascade="all, delete-orphan",
    )
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
        currency_name = self.currency.name if self.currency else "No currency"
        return f"<Faction(id={self.faction_id}, name={self.name}, currency={currency_name})>"

    def __str__(self) -> str:
        return self.name
