from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, DateTime, ForeignKey, Index, Integer, String,
                        Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..clock import utcnow
from ..database import Base


class Schematic(Base):
    """A schematic of the gallery: a structure file (.nbt) shared by a player,
    with its successive versions, its tags and an optional preview image.

    The files themselves are on disk (see app.crud.schematic): the database
    only keeps their names.
    """

    __tablename__ = "schematics"

    schematic_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    author_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    # The stored preview image ("<random>.png"), and its media type
    preview_file: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    preview_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    author = relationship("User", lazy="joined")
    versions = relationship(
        "SchematicVersion",
        back_populates="schematic",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SchematicVersion.number",
        lazy="selectin",
    )
    tags = relationship(
        "SchematicTag",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SchematicTag.tag",
        lazy="selectin",
    )

    @property
    def current_version(self) -> Optional["SchematicVersion"]:
        return self.versions[-1] if self.versions else None

    @property
    def tag_names(self) -> list[str]:
        return [t.tag for t in self.tags]

    def __repr__(self) -> str:
        return f"<Schematic(id={self.schematic_id}, title={self.title})>"


class SchematicVersion(Base):
    """One uploaded file of a schematic. Versions are numbered from 1 and
    never rewritten: a new file is a new version."""

    __tablename__ = "schematic_versions"
    __table_args__ = (
        UniqueConstraint("schematic_id", "number", name="uq_schematic_version"),
    )

    version_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schematic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("schematics.schematic_id", ondelete="CASCADE"),
        nullable=False,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)

    # On disk: "<random>.nbt"; the name the player gave it is only displayed
    file_name: Mapped[str] = mapped_column(String(64), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    # Read from the file when it is uploaded
    size_x: Mapped[int] = mapped_column(Integer, nullable=False)
    size_y: Mapped[int] = mapped_column(Integer, nullable=False)
    size_z: Mapped[int] = mapped_column(Integer, nullable=False)
    block_count: Mapped[int] = mapped_column(Integer, nullable=False)
    data_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    uploaded_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    # Checked against the railway standards by a train admin. It belongs to
    # the version: a new file has not been checked.
    compliant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    compliant_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    compliant_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    schematic = relationship("Schematic", back_populates="versions")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id], lazy="joined")

    def __repr__(self) -> str:
        return f"<SchematicVersion(schematic={self.schematic_id}, v{self.number})>"


class SchematicTag(Base):
    """A tag of a schematic ("train", "gare", "fret"...): lower case."""

    __tablename__ = "schematic_tags"
    __table_args__ = (Index("ix_schematic_tags_tag", "tag"),)

    schematic_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("schematics.schematic_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(String(30), primary_key=True)
