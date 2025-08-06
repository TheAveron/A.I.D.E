from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..database import OfferHistory
from ..misc import OfferAction
from ..schemas import OfferHistoryCreate


def create_offer_history(
    db: Session,
    offer_id: int,
    action: OfferAction,
    actor_user_id: Optional[int] = None,
    actor_faction_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> OfferHistory:
    history = OfferHistory(
        offer_id=offer_id,
        actor_user_id=actor_user_id,
        actor_faction_id=actor_faction_id,
        action=action,
        notes=notes,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_offer_history(db: Session, history_id: int) -> OfferHistory:
    history = (
        db.query(OfferHistory).filter(OfferHistory.history_id == history_id).first()
    )
    if not history:
        raise HTTPException(status_code=404, detail="Offer history not found")
    return history


def get_offer_histories(
    db: Session,
    actor_user_id: Optional[int] = None,
    actor_faction_id: Optional[int] = None,
    offer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[OfferHistory]:
    query = db.query(OfferHistory)

    if actor_user_id is not None:
        query = query.filter(OfferHistory.actor_user_id == actor_user_id)
    if actor_faction_id is not None:
        query = query.filter(OfferHistory.actor_faction_id == actor_faction_id)
    if offer_id is not None:
        query = query.filter(OfferHistory.offer_id == offer_id)

    histories = query.offset(skip).limit(limit).all()

    if not histories:
        raise HTTPException(status_code=404, detail="No offer history found")

    return histories


def update_offer_history(
    db: Session, history_id: int, update_data: OfferHistoryCreate
) -> OfferHistory:
    history = get_offer_history(db, history_id)

    history.offer_id = update_data.offer_id
    history.actor_user_id = update_data.actor_user_id
    history.actor_faction_id = update_data.actor_faction_id
    history.action = update_data.action
    history.notes = update_data.notes

    db.commit()
    db.refresh(history)
    return history


def delete_offer_history(db: Session, history_id: int) -> None:
    history = get_offer_history(db, history_id)
    db.delete(history)
    db.commit()
