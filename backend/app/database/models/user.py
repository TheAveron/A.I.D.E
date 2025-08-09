from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class User(Base):
    """
    SQLAlchemy User model representing a user in the system.
    """

    __tablename__ = "users"
    __table_args__ = (Index("ix_users_username_email", "username", "email"),)

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    faction_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("factions.faction_id"), nullable=True
    )
    faction = relationship("Faction", back_populates="users")

    role_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("roles.role_id"), nullable=True
    )
    role = relationship("Role", back_populates="users")

    offers = relationship(
        "Offer",
        back_populates="user",
        foreign_keys="[Offer.user_id]",
    )

    accepted_offers = relationship(
        "Offer",
        back_populates="accepted_by_user_obj",
        foreign_keys="[Offer.accepted_by_user_id]",
    )

    def __repr__(self) -> str:
        return f"<User(username={self.username}, email={self.email}, faction={self.faction_id})>"

    def __str__(self) -> str:
        return f"User: {self.username} ({self.email})"
