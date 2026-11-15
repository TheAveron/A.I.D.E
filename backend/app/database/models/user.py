from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..clock import utcnow
from ..database import Base
from .global_role import GlobalRole, GlobalRoleName


class User(Base):
    """
    SQLAlchemy User model representing a user in the system.
    """

    __tablename__ = "users"
    __table_args__ = (Index("ix_users_username_email", "username", "email"),)

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
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

    # Server-wide roles (admin, train admin...), see GlobalRole
    global_roles = relationship(
        "GlobalRole",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def global_role_names(self) -> list[str]:
        return sorted(r.role for r in self.global_roles)

    def has_global_role(self, role: str) -> bool:
        return any(r.role == role for r in self.global_roles)

    def add_global_role(self, role: str) -> None:
        if not self.has_global_role(role):
            self.global_roles.append(GlobalRole(role=role))

    def remove_global_role(self, role: str) -> None:
        for held in [r for r in self.global_roles if r.role == role]:
            self.global_roles.remove(held)

    @property
    def is_admin(self) -> bool:
        return self.has_global_role(GlobalRoleName.ADMIN.value)

    @is_admin.setter
    def is_admin(self, value: bool) -> None:
        if value:
            self.add_global_role(GlobalRoleName.ADMIN.value)
        else:
            self.remove_global_role(GlobalRoleName.ADMIN.value)

    def __repr__(self) -> str:
        return f"<User(username={self.username}, email={self.email}, faction={self.faction_id})>"

    def __str__(self) -> str:
        return f"User: {self.username} ({self.email})"
