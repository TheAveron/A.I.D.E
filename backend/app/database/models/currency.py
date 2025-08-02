from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Currency(Base):
    """
    Represents a tradable currency in the marketplace.
    """

    __tablename__ = "currencies"

    name: Mapped[str] = mapped_column(String(50), primary_key=True, index=True)
    faction_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("factions.faction_id"),
        nullable=True,
        index=True,
        unique=True,
    )
    faction = relationship("Faction", back_populates="currencies")
    symbol: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    total_in_circulation: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    offers = relationship(
        "Offer", back_populates="currency", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Currency(name='{self.name}', symbol='{self.symbol}', "

    def __str__(self) -> str:
        symbol_part = f" ({self.symbol})" if self.symbol else ""
        return f"Currency: {self.name}{symbol_part}"
