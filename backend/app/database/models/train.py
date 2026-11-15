from datetime import datetime
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..clock import utcnow
from ..database import Base

MAINTENANCE_LINE = "Z"


class Line(Base):
    """A railway line: a corridor through an ordered list of stations."""

    __tablename__ = "lines"

    line_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # "A".."Y", optionally followed by 1-9 for a branch ("A2"); "Z" is the
    # maintenance line. Always upper case.
    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    # "#rrggbb", for maps and display boards
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # The faction that looks after the line, if any
    owner_faction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("factions.faction_id", ondelete="SET NULL"), nullable=True
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

    stops = relationship(
        "LineStop",
        back_populates="line",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LineStop.position",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Line(code={self.code})>"


class LineStop(Base):
    """One station on a line, at a given place in the order (0 = first end)."""

    __tablename__ = "line_stops"
    __table_args__ = (
        UniqueConstraint("line_id", "station_id", name="uq_line_stop_station"),
    )

    stop_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    line_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("lines.line_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line = relationship("Line", back_populates="stops")

    # No cascade: a station that still serves a line cannot be deleted
    station_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stations.station_id"), nullable=False, index=True
    )
    station = relationship("Station", lazy="joined")

    position: Mapped[int] = mapped_column(Integer, nullable=False)


class Train(Base):
    """A train. The name shown in stations is built from its parts."""

    __tablename__ = "trains"
    __table_args__ = (
        CheckConstraint(
            "(owner_user_id IS NOT NULL AND owner_faction_id IS NULL) OR "
            "(owner_user_id IS NULL AND owner_faction_id IS NOT NULL)",
            name="check_train_one_owner",
        ),
        CheckConstraint("number BETWEEN 1 AND 99", name="check_train_number"),
        # Numbers are unique per line among the trains still running; a retired
        # train frees its number.
        Index(
            "uq_trains_active_line_number",
            "line_id",
            "number",
            unique=True,
            postgresql_where=text("retired_at IS NULL"),
            sqlite_where=text("retired_at IS NULL"),
        ),
        Index(
            "uq_trains_active_legacy_id",
            "legacy_id",
            unique=True,
            postgresql_where=text("retired_at IS NULL AND legacy_id IS NOT NULL"),
            sqlite_where=text("retired_at IS NULL AND legacy_id IS NOT NULL"),
        ),
    )

    train_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    line_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lines.line_id"), nullable=False, index=True
    )
    line = relationship("Line", lazy="joined")

    # A TrainService value; None on the maintenance line
    service: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    common_name: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    # The name under the old convention ("MMP1-1"), for trains that existed
    legacy_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    owner_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=True, index=True
    )
    owner_faction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("factions.faction_id"), nullable=True, index=True
    )

    owner_user = relationship("User", foreign_keys=[owner_user_id], lazy="joined")
    owner_faction = relationship(
        "Faction", foreign_keys=[owner_faction_id], lazy="joined"
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
    # Set when the train is taken out of service (it stays for the history)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    history = relationship(
        "TrainHistory",
        back_populates="train",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TrainHistory.history_id",
    )

    @property
    def line_code(self) -> str:
        return self.line.code

    @property
    def owner_name(self) -> Optional[str]:
        if self.owner_user is not None:
            return self.owner_user.username
        if self.owner_faction is not None:
            return self.owner_faction.name
        return None

    @property
    def display_name(self) -> str:
        """`A-E07 Aurore`, `A2-O12`, `Z-01`."""
        name = f"{self.line.code}-{self.service or ''}{self.number:02d}"
        return f"{name} {self.common_name}" if self.common_name else name

    def __repr__(self) -> str:
        return f"<Train(id={self.train_id}, name={self.display_name})>"


class TrainHistory(Base):
    """What happened to a train: created, renamed (line / service), retired..."""

    __tablename__ = "train_history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    train_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("trains.train_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    train = relationship("Train", back_populates="history")

    # A TrainAction value
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    old_name: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    new_name: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    actor_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
