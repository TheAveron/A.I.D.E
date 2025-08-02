from typing import Any, Optional

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Role(Base):
    """
    Represents a role within a faction, defining permissions for users.
    """

    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(50), nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    permissions: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    faction_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("factions.faction_id"), nullable=False
    )

    # Relationships
    faction = relationship("Faction", back_populates="roles")
    users = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(name={self.name}, faction={self.faction.name if self.faction else None})>"

    def __str__(self) -> str:
        return (
            f"Role: {self.name} ({self.faction.name if self.faction else 'No faction'})"
        )
