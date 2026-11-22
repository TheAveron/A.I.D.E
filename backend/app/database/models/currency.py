from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, DateTime, ForeignKey, Index, Integer, String,
                        UniqueConstraint, text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import expression

from ..clock import utcnow
from ..database import Base


class Currency(Base):
    """
    Represents a tradable currency in the marketplace.

    Several factions may use the same currency (see `CurrencyFaction`); the
    ones flagged as issuers are the ones allowed to change it. Offers,
    transactions and the history point at `currency_id`, so the name can
    change at any time.
    """

    __tablename__ = "currencies"

    currency_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    symbol: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    total_in_circulation: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    links = relationship(
        "CurrencyFaction",
        back_populates="currency",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="CurrencyFaction.joined_at",
    )

    offers = relationship("Offer", back_populates="currency", passive_deletes=True)

    history = relationship(
        "CurrencyHistory",
        back_populates="currency",
        cascade="all, delete-orphan",
        foreign_keys="[CurrencyHistory.currency_id]",
    )

    link_requests = relationship(
        "CurrencyLinkRequest",
        back_populates="currency",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def issuer_faction_ids(self) -> list[int]:
        return [link.faction_id for link in self.links if link.is_issuer]

    @property
    def faction_ids(self) -> list[int]:
        return [link.faction_id for link in self.links]

    def __repr__(self) -> str:
        return (
            f"<Currency(id={self.currency_id}, name='{self.name}', "
            f"symbol='{self.symbol}')>"
        )

    def __str__(self) -> str:
        symbol_part = f" ({self.symbol})" if self.symbol else ""
        return f"Currency: {self.name}{symbol_part}"


class CurrencyFaction(Base):
    """A faction using a currency; issuers may change the currency.

    A faction uses at most one currency (`uq_currency_factions_faction`); a
    currency always keeps at least one issuer, which the API enforces.
    """

    __tablename__ = "currency_factions"
    __table_args__ = (
        UniqueConstraint("faction_id", name="uq_currency_factions_faction"),
    )

    currency_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("currencies.currency_id", ondelete="CASCADE"),
        primary_key=True,
    )
    faction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("factions.faction_id", ondelete="CASCADE"),
        primary_key=True,
    )
    is_issuer: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=expression.false(), nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )

    currency = relationship("Currency", back_populates="links")
    faction = relationship("Faction", back_populates="currency_link")

    def __repr__(self) -> str:
        return (
            f"<CurrencyFaction(currency={self.currency_id}, "
            f"faction={self.faction_id}, issuer={self.is_issuer})>"
        )


class CurrencyLinkRequest(Base):
    """A pending wish to have a faction use a currency.

    Either the faction asks (`kind` "REQUEST", an issuer accepts) or an issuer
    proposes (`kind` "INVITATION", the faction accepts).
    """

    __tablename__ = "currency_link_requests"
    __table_args__ = (
        # One open request per (currency, faction) at a time
        Index(
            "uq_currency_link_requests_one_pending",
            "currency_id",
            "faction_id",
            unique=True,
            postgresql_where=text("status = 'PENDING'"),
            sqlite_where=text("status = 'PENDING'"),
        ),
    )

    request_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    currency_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("currencies.currency_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    faction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("factions.faction_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # A CurrencyLinkKind value
    kind: Mapped[str] = mapped_column(String(12), nullable=False)
    # A JoinRequestStatus value (same life as a join request)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="PENDING")

    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, nullable=False
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decided_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )

    currency = relationship("Currency", back_populates="link_requests")
    faction = relationship("Faction")

    @property
    def currency_name(self) -> Optional[str]:
        return self.currency.name if self.currency else None

    @property
    def faction_name(self) -> Optional[str]:
        return self.faction.name if self.faction else None

    def __repr__(self) -> str:
        return (
            f"<CurrencyLinkRequest(id={self.request_id}, kind={self.kind}, "
            f"currency={self.currency_id}, faction={self.faction_id}, "
            f"status={self.status})>"
        )
