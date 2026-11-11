from typing import Optional

from sqlalchemy.orm import Session

from ..database import CurrencyHistory


def create_currency_history(
    db: Session,
    currency_name: str,
    old_total_in_circulation: int,
    new_total_in_circulation: int,
    actor_user_id: Optional[int] = None,
    notes: Optional[str] = None,
    commit: bool = True,
) -> CurrencyHistory:
    """Record a change to a currency's declared total in circulation.

    Pass `commit=False` to have the entry written in the caller's own
    transaction (so the change and its audit entry succeed or fail
    together) - the caller is then responsible for committing.
    """
    history = CurrencyHistory(
        currency_name=currency_name,
        actor_user_id=actor_user_id,
        old_total_in_circulation=old_total_in_circulation,
        new_total_in_circulation=new_total_in_circulation,
        notes=notes,
    )
    db.add(history)
    if commit:
        db.commit()
        db.refresh(history)
    return history


def get_currency_histories(
    db: Session,
    currency_name: str,
    skip: int = 0,
    limit: int = 50,
) -> list[CurrencyHistory]:
    return (
        db.query(CurrencyHistory)
        .filter(CurrencyHistory.currency_name == currency_name)
        .order_by(CurrencyHistory.timestamp.desc(), CurrencyHistory.history_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
