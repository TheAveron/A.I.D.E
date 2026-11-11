from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..database import Currency
from ..schemas import CurrencyCreate, CurrencyUpdate
from .currency_history import create_currency_history


def get_currency(db: Session, currency_name: str) -> Optional[Currency]:
    return db.query(Currency).filter(Currency.name == currency_name).first()


def get_currency_by_faction(db: Session, faction_id: int) -> Optional[Currency]:
    return db.query(Currency).filter(Currency.faction_id == faction_id).first()


def get_currencies(db: Session, skip: int = 0, limit: int = 100) -> list[Currency]:
    return db.query(Currency).offset(skip).limit(limit).all()


def create_currency(
    db: Session, currency_in: CurrencyCreate, actor_user_id: Optional[int] = None
) -> Currency:
    db_currency = Currency(
        name=currency_in.name,
        symbol=currency_in.symbol,
        faction_id=currency_in.faction_id,
        total_in_circulation=currency_in.total_in_circulation,
    )
    db.add(db_currency)

    # Record the initially declared figure so the audit trail starts at
    # the beginning rather than at the first later edit.
    if db_currency.total_in_circulation:
        create_currency_history(
            db,
            currency_name=db_currency.name,
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
    currency_name: str,
    currency_in: CurrencyUpdate,
    actor_user_id: Optional[int] = None,
) -> Currency:
    db_currency = get_currency(db, currency_name)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    old_total = db_currency.total_in_circulation

    if currency_in.symbol is not None:
        db_currency.symbol = currency_in.symbol
    if currency_in.total_in_circulation is not None:
        db_currency.total_in_circulation = currency_in.total_in_circulation
    if currency_in.name is not None:
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
            currency_name=db_currency.name,
            old_total_in_circulation=old_total,
            new_total_in_circulation=currency_in.total_in_circulation,
            actor_user_id=actor_user_id,
            commit=False,
        )

    db.commit()
    db.refresh(db_currency)
    return db_currency


def delete_currency(db: Session, currency_name: str) -> None:
    db_currency = get_currency(db, currency_name)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    db.delete(db_currency)
    db.commit()
