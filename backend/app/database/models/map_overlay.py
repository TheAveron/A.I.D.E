from datetime import datetime
from typing import Optional

from sqlalchemy import (JSON, CheckConstraint, DateTime, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..clock import utcnow
from ..database import Base


class MapTerritory(Base):
    """The outline of a faction's land on one of the maps.

    `points` is the polygon: a list of [x, z] block coordinates, in order.
    """

    __tablename__ = "map_territories"
    __table_args__ = (
        UniqueConstraint("map_name", "faction_id", "name", name="uq_territory_name"),
    )

    territory_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # The folder of the map in documents/maps (e.g. "OAOS_zoom")
    map_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # "#rrggbb"; empty: the front picks one from the faction
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    faction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("factions.faction_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    faction = relationship("Faction")

    points: Mapped[list] = mapped_column(JSON, nullable=False)

    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    @property
    def faction_name(self) -> Optional[str]:
        return self.faction.name if self.faction else None


class MapMarker(Base):
    """A point of interest: a base, a mine, a portal... owned by a faction
    or by a player (never both)."""

    __tablename__ = "map_markers"
    __table_args__ = (
        CheckConstraint(
            "(faction_id IS NOT NULL AND user_id IS NULL) OR "
            "(faction_id IS NULL AND user_id IS NOT NULL)",
            name="ck_map_marker_one_owner",
        ),
    )

    marker_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    map_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    label: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # A MarkerKind value
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="other")

    x: Mapped[int] = mapped_column(Integer, nullable=False)
    z: Mapped[int] = mapped_column(Integer, nullable=False)

    faction_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("factions.faction_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    faction = relationship("Faction")
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user = relationship("User")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    @property
    def owner_name(self) -> Optional[str]:
        if self.faction_id is not None:
            return self.faction.name if self.faction else None
        return self.user.username if self.user else None
