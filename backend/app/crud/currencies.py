from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional

from ..database import Currency
from ..schemas import CurrencyCreate, CurrencyUpdate


def get_currency(db: Session, currency_name: str) -> Optional[Currency]:
    return db.query(Currency).filter(Currency.name == currency_name).first()


def get_currencies(db: Session, skip: int = 0, limit: int = 100) -> list[Currency]:
    return db.query(Currency).offset(skip).limit(limit).all()


def create_currency(db: Session, currency_in: CurrencyCreate) -> Currency:
    db_currency = Currency(
        name=currency_in.name,
        symbol=currency_in.symbol,
        faction_id=currency_in.faction_id,
    )
    db.add(db_currency)
    db.commit()
    db.refresh(db_currency)
    return db_currency


def update_currency(
    db: Session, currency_name: str, currency_in: CurrencyUpdate
) -> Currency:
    db_currency = get_currency(db, currency_name)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    if currency_in.symbol is not None:
        db_currency.symbol = currency_in.symbol
    if currency_in.faction_id is not None:
        db_currency.faction_id = currency_in.faction_id

    db.commit()
    db.refresh(db_currency)
    return db_currency


def delete_currency(db: Session, currency_name: str) -> None:
    db_currency = get_currency(db, currency_name)
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    db.delete(db_currency)
    db.commit()
