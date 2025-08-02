import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Index, Integer,
                        String)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...misc import OfferAction
from ..database import Base

offer_action_enum = ENUM(OfferAction, name="offer_action_enum", create_type=True)


class OfferHistory(Base):
    """
    Represents a log entry of an action taken on an offer.
    """

    __tablename__ = "offer_history"
    __table_args__ = (
        CheckConstraint(
            "(actor_user_id IS NOT NULL AND actor_faction_id IS NULL) OR "
            "(actor_user_id IS NULL AND actor_faction_id IS NOT NULL)",
            name="check_only_one_actor",
        ),
        Index("ix_offer_history_offer_id_timestamp", "offer_id", "timestamp"),
    )

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Related offer
    offer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("offers.offer_id"), nullable=False, index=True
    )
    offer = relationship("Offer", back_populates="history", foreign_keys=[offer_id])

    # Actor (user or faction)
    actor_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True, index=True
    )
    actor_user = relationship("User", foreign_keys=[actor_user_id])

    actor_faction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("factions.faction_id"), nullable=True, index=True
    )
    actor_faction = relationship("Faction", foreign_keys=[actor_faction_id])

    # Action taken
    action: Mapped[OfferAction] = mapped_column(offer_action_enum, nullable=False)

    # When it happened
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Optional notes
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        actor = (
            self.actor_user.username
            if self.actor_user
            else (self.actor_faction.name if self.actor_faction else "Unknown")
        )
        return (
            f"<OfferHistory(id={self.history_id}, offer_id={self.offer_id}, "
            f"actor={actor}, action={self.action.value}, timestamp={self.timestamp})>"
        )

    def __str__(self) -> str:
        return (
            f"Offer {self.offer_id} - {self.action.value} by actor at {self.timestamp}"
        )
