from typing import Optional

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import Offer, OfferHistory, User
from ..misc import OfferAction
from ..schemas import OfferHistoryCreate


def create_offer_history(
    db: Session,
    offer_id: int,
    action: OfferAction,
    actor_user_id: Optional[int] = None,
    actor_faction_id: Optional[int] = None,
    notes: Optional[str] = None,
    commit: bool = True,
) -> OfferHistory:
    """Record an action on an offer.

    Pass `commit=False` to write the entry inside the caller's transaction,
    so the action and its history entry succeed or fail together.
    """
    history = OfferHistory(
        offer_id=offer_id,
        actor_user_id=actor_user_id,
        actor_faction_id=actor_faction_id,
        action=action,
        notes=notes,
    )
    db.add(history)
    if commit:
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
    viewer: User,
    actor_user_id: Optional[int] = None,
    actor_faction_id: Optional[int] = None,
    offer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[OfferHistory]:
    """History entries the viewer is allowed to see, newest first.

    Visible: entries about the viewer's own offers or made by the viewer,
    plus - for members whose role has `view_transactions` - entries about
    their faction's offers or made by their faction. The optional filters
    only narrow that scope; asking for someone else's id yields nothing.
    """
    query = db.query(OfferHistory).join(Offer, OfferHistory.offer_id == Offer.offer_id)

    scope = [
        OfferHistory.actor_user_id == viewer.user_id,
        Offer.user_id == viewer.user_id,
    ]
    if viewer.faction_id and viewer.role and viewer.role.view_transactions:
        scope += [
            OfferHistory.actor_faction_id == viewer.faction_id,
            Offer.faction_id == viewer.faction_id,
        ]
    query = query.filter(or_(*scope))

    if actor_user_id is not None:
        query = query.filter(OfferHistory.actor_user_id == actor_user_id)
    if actor_faction_id is not None:
        query = query.filter(OfferHistory.actor_faction_id == actor_faction_id)
    if offer_id is not None:
        query = query.filter(OfferHistory.offer_id == offer_id)

    return (
        query.order_by(OfferHistory.timestamp.desc(), OfferHistory.history_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


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
