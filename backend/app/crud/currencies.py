"""Currencies, and the factions that use or issue them.

A currency is used by one or more factions (a faction uses at most one).
The issuers among them run it: the members of an issuer faction who hold
`manage_funds` may change it, and so may a money admin, for any currency.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import (Currency, CurrencyFaction, GlobalRoleName, Offer,
                        Transaction, User)
from ..misc import FactionPermission, check_faction_permission
from ..schemas import CurrencyCreate, CurrencyUpdate
from .currency_history import create_currency_history


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


# ── Reading ───────────────────────────────────────────────────────────────


def get_currency(db: Session, currency_id: int) -> Optional[Currency]:
    return db.query(Currency).filter(Currency.currency_id == currency_id).first()


def get_currency_by_name(db: Session, name: str) -> Optional[Currency]:
    return db.query(Currency).filter(Currency.name == name).first()


def get_currency_by_faction(db: Session, faction_id: int) -> Optional[Currency]:
    """The currency a faction uses, or None."""
    return (
        db.query(Currency)
        .join(CurrencyFaction, CurrencyFaction.currency_id == Currency.currency_id)
        .filter(CurrencyFaction.faction_id == faction_id)
        .first()
    )


def get_link(
    db: Session, currency_id: int, faction_id: int
) -> Optional[CurrencyFaction]:
    return (
        db.query(CurrencyFaction)
        .filter(
            CurrencyFaction.currency_id == currency_id,
            CurrencyFaction.faction_id == faction_id,
        )
        .first()
    )


def get_currencies(db: Session, skip: int = 0, limit: int = 100) -> list[Currency]:
    return db.query(Currency).order_by(Currency.name).offset(skip).limit(limit).all()


def is_currency_referenced(db: Session, currency_id: int) -> bool:
    """Whether offers or transactions still point at this currency."""
    return bool(
        db.query(Offer.offer_id).filter(Offer.currency_id == currency_id).first()
        or db.query(Transaction.transaction_id)
        .filter(Transaction.currency_id == currency_id)
        .first()
    )


# ── Who may do what ───────────────────────────────────────────────────────


def is_money_admin(user: User) -> bool:
    return user.has_global_role(GlobalRoleName.MONEY_ADMIN.value)


def holds_manage_funds(user: User, faction_id: Optional[int]) -> bool:
    """Whether `user` holds `manage_funds` in the faction `faction_id`."""
    if faction_id is None:
        return False
    try:
        check_faction_permission(
            user, FactionPermission.MANAGE_FUNDS, target_faction_id=faction_id
        )
    except HTTPException:
        return False
    return True


def is_issuer_manager(user: User, currency: Currency) -> bool:
    """Whether `user` runs `currency` through their faction: the faction
    issues it and their role there holds `manage_funds`."""
    return user.faction_id in currency.issuer_faction_ids and holds_manage_funds(
        user, user.faction_id
    )


def can_manage(user: User, currency: Currency) -> bool:
    return is_issuer_manager(user, currency) or is_money_admin(user)


def require_manager(user: User, currency: Currency) -> bool:
    """Raise 403 unless `user` may change `currency`.

    Returns True when only the money admin role lets them through: the caller
    then records the action in the audit trail, like any staff override.
    """
    if is_issuer_manager(user, currency):
        return False
    if is_money_admin(user):
        return True
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only an issuer of this currency (with manage_funds) or a money "
        "admin may change it",
    )


def can_view_details(user: User, currency: Currency) -> bool:
    """The declared total and its history: for the managers of the factions
    that use the currency, and for money admins."""
    return is_money_admin(user) or (
        user.faction_id in currency.faction_ids
        and holds_manage_funds(user, user.faction_id)
    )


# ── Changing currencies ───────────────────────────────────────────────────


def create_currency(
    db: Session, currency_in: CurrencyCreate, actor_user_id: Optional[int] = None
) -> Currency:
    """A new currency, issued by the faction `currency_in.faction_id` alone."""
    if get_currency_by_name(db, currency_in.name):
        raise _conflict("Currency already exists")
    if get_currency_by_faction(db, currency_in.faction_id):
        raise _conflict("This faction already uses a currency")

    db_currency = Currency(
        name=currency_in.name,
        symbol=currency_in.symbol,
        total_in_circulation=currency_in.total_in_circulation,
    )
    db_currency.links.append(
        CurrencyFaction(faction_id=currency_in.faction_id, is_issuer=True)
    )
    db.add(db_currency)

    try:
        db.flush()  # assigns currency_id, checks the unique name and faction
    except IntegrityError:
        # Lost a race against another request creating the same currency.
        db.rollback()
        raise _conflict("Currency already exists or the faction already uses one")

    # Record the initially declared figure so the audit trail starts at
    # the beginning rather than at the first later edit.
    if db_currency.total_in_circulation:
        create_currency_history(
            db,
            currency_id=db_currency.currency_id,
            old_total_in_circulation=0,
            new_total_in_circulation=db_currency.total_in_circulation,
            actor_user_id=actor_user_id,
            notes="Initial value at currency creation",
            commit=False,
        )

    db.commit()
    db.refresh(db_currency)
    return db_currency


def update_currency(
    db: Session,
    currency_id: int,
    currency_in: CurrencyUpdate,
    actor_user_id: Optional[int] = None,
) -> Currency:
    db_currency = get_currency(db, currency_id)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    old_total = db_currency.total_in_circulation

    if currency_in.symbol is not None:
        db_currency.symbol = currency_in.symbol
    if currency_in.total_in_circulation is not None:
        db_currency.total_in_circulation = currency_in.total_in_circulation

    if currency_in.name is not None and currency_in.name != db_currency.name:
        # Offers, transactions and the history point at currency_id: a
        # rename carries them along. Only the name itself must stay unique.
        other = get_currency_by_name(db, currency_in.name)
        if other and other.currency_id != db_currency.currency_id:
            raise _conflict("Currency already exists")
        create_currency_history(
            db,
            currency_id=db_currency.currency_id,
            old_total_in_circulation=old_total,
            new_total_in_circulation=old_total,
            actor_user_id=actor_user_id,
            notes=f"Renommée : « {db_currency.name} » → « {currency_in.name} »",
            commit=False,
        )
        db_currency.name = currency_in.name

    # Only log real changes: resubmitting the same figure isn't an event
    # worth an audit entry. Written in the same transaction as the update
    # so the change can never exist without its audit entry.
    if (
        currency_in.total_in_circulation is not None
        and currency_in.total_in_circulation != old_total
    ):
        create_currency_history(
            db,
            currency_id=db_currency.currency_id,
            old_total_in_circulation=old_total,
            new_total_in_circulation=currency_in.total_in_circulation,
            actor_user_id=actor_user_id,
            notes=(currency_in.notes or "").strip() or None,
            commit=False,
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _conflict("Currency already exists")
    db.refresh(db_currency)
    return db_currency


def delete_currency(db: Session, currency_id: int) -> None:
    db_currency = get_currency(db, currency_id)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    if is_currency_referenced(db, currency_id):
        raise _conflict(
            "This currency is still used by offers or transactions and can't be deleted"
        )
    db.delete(db_currency)
    db.commit()


# ── The factions of a currency (nothing is committed here) ────────────────


def add_faction(
    db: Session, currency: Currency, faction_id: int, is_issuer: bool = False
) -> CurrencyFaction:
    """Have a faction use `currency`. A faction uses one currency at most."""
    current = get_currency_by_faction(db, faction_id)
    if current is not None:
        if current.currency_id == currency.currency_id:
            raise _conflict("This faction already uses this currency")
        raise _conflict(
            "This faction already uses another currency: it must leave it first"
        )
    link = CurrencyFaction(faction_id=faction_id, is_issuer=is_issuer)
    currency.links.append(link)
    return link


def _require_link(db: Session, currency: Currency, faction_id: int) -> CurrencyFaction:
    link = get_link(db, currency.currency_id, faction_id)
    if not link:
        raise HTTPException(
            status_code=404, detail="This faction does not use this currency"
        )
    return link


def _require_another_issuer(currency: Currency, faction_id: int) -> None:
    if currency.issuer_faction_ids == [faction_id]:
        raise _conflict(
            "A currency keeps at least one issuer: make another faction an "
            "issuer first"
        )


def remove_faction(db: Session, currency: Currency, faction_id: int) -> None:
    link = _require_link(db, currency, faction_id)
    if link.is_issuer:
        _require_another_issuer(currency, faction_id)
    currency.links.remove(link)


def set_issuer(
    db: Session, currency: Currency, faction_id: int, is_issuer: bool
) -> CurrencyFaction:
    link = _require_link(db, currency, faction_id)
    if link.is_issuer and not is_issuer:
        _require_another_issuer(currency, faction_id)
    link.is_issuer = is_issuer
    return link
