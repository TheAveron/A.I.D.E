from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, DateTime, ForeignKey, Integer, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Role(Base):
    """
    Represents a role within a faction, defining permissions for users.
    """

    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("faction_id", "name", name="uq_faction_role_name"),
    )

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(50), nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    accept_offers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    create_offers: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manage_funds: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    handle_members: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manage_roles: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manage_docs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_transactions: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    faction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("factions.faction_id", ondelete="CASCADE"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    faction = relationship("Faction", back_populates="roles")
    users = relationship("User", back_populates="role", passive_deletes=True)

    def __repr__(self) -> str:
        return f"<Role(id={self.role_id}, name={self.name}, faction={self.faction_id})>"

    def __str__(self) -> str:
        return f"{self.name} ({self.faction.name if self.faction else 'No faction'})"
