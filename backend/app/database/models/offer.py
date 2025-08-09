from datetime import datetime
from typing import Optional

from sqlalchemy import (JSON, CheckConstraint, DateTime, Float, ForeignKey,
                        Index, Integer, String)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...misc import OfferStatus, OfferType
from ..database import Base

offer_type_enum = ENUM(OfferType, name="offer_type_enum", create_type=True)
offer_status_enum = ENUM(OfferStatus, name="offer_status_enum", create_type=True)


class Offer(Base):
    """
    SQLAlchemy Offer model representing a marketplace offer.
    """

    __tablename__ = "offers"
    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND faction_id IS NULL) OR "
            "(user_id IS NULL AND faction_id IS NOT NULL)",
            name="check_only_one_creator",
        ),
        Index("ix_offers_status_type", "status", "offer_type"),
    )

    offer_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True, index=True
    )
    user = relationship("User", back_populates="offers", foreign_keys=[user_id])

    faction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("factions.faction_id"), nullable=True, index=True
    )
    faction = relationship(
        "Faction", back_populates="offers", foreign_keys=[faction_id]
    )

    offer_type: Mapped[OfferType] = mapped_column(
        offer_type_enum,
        nullable=False,
        index=True,
    )
    item_description: Mapped[str] = mapped_column(String, nullable=False)

    currency_name: Mapped[str] = mapped_column(
        String(50), ForeignKey("currencies.name"), nullable=False, index=True
    )
    currency = relationship("Currency", back_populates="offers", passive_deletes=True)

    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    init_quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    allowed_parties: Mapped[Optional[list[int]]] = mapped_column(JSON, nullable=True)

    status: Mapped[OfferStatus] = mapped_column(
        offer_status_enum,
        default=OfferStatus.OPEN,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    accepted_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True, index=True
    )
    accepted_by_user_obj = relationship(
        "User",
        foreign_keys=[accepted_by_user_id],
        back_populates="accepted_offers",
    )

    accepted_by_faction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("factions.faction_id"), nullable=True, index=True
    )
    accepted_by_faction_obj = relationship(
        "Faction",
        back_populates="accepted_offers",
        foreign_keys=[accepted_by_faction_id],
    )

    transactions = relationship(
        "Transaction",
        back_populates="offer",
        cascade="all, delete-orphan",
        foreign_keys="[Transaction.offer_id]",
    )

    history = relationship(
        "OfferHistory", back_populates="offer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        creator = (
            self.user.username
            if self.user
            else (self.faction.name if self.faction else "Unknown")
        )
        return (
            f"<Offer(id={self.offer_id}, creator={creator}, type={self.offer_type.value}, "
            f"item={self.item_description}, price={self.price_per_unit}, "
            f"quantity={self.quantity}, status={self.status.value})>"
        )

    def __str__(self) -> str:
        return (
            f"Offer {self.offer_id}: {self.offer_type.value} {self.quantity} @ "
            f"{self.price_per_unit} {self.currency_name} ({self.status.value})"
        )

    def is_open(self) -> bool:
        """Check if the offer is still open."""
        return self.status == OfferStatus.OPEN
