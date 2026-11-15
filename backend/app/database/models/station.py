from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..clock import utcnow
from ..database import Base


class Station(Base):
    """A railway station, placed in the world by its coordinates."""

    __tablename__ = "stations"
    station_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Minecraft block coordinates; y (height) is optional
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    z: Mapped[int] = mapped_column(Integer, nullable=False)
    # A StationDimension value ("overworld", "nether", "end")
    dimension: Mapped[str] = mapped_column(
        String(20), nullable=False, default="overworld"
    )

    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    platforms = relationship(
        "Platform",
        back_populates="station",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Platform.name",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Station(id={self.station_id}, name={self.name})>"


# "Gare du Nord" and "gare du nord" are the same station
Index("uq_stations_name_lower", func.lower(Station.name), unique=True)


class Platform(Base):
    """A platform of a station ("1", "A"...), so travellers know where to go."""

    __tablename__ = "platforms"
    __table_args__ = (
        UniqueConstraint("station_id", "name", name="uq_platform_station_name"),
    )

    platform_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    station_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    station = relationship("Station", back_populates="platforms")

    name: Mapped[str] = mapped_column(String(20), nullable=False)
    # Free text: direction, access, what is around...
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    def __repr__(self) -> str:
        return f"<Platform(station={self.station_id}, name={self.name})>"
