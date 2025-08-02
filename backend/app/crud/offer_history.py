from typing import Optional

from sqlalchemy.orm import Session

from ..database import OfferHistory
from ..misc import OfferAction


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


def get_offer_history(db: Session, offer_id: int) -> list[OfferHistory]:
    return (
        db.query(OfferHistory)
        .filter(OfferHistory.offer_id == offer_id)
        .order_by(OfferHistory.timestamp.desc())
        .all()
    )
