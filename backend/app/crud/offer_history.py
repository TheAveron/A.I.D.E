from sqlalchemy.orm import Session

from ..database import OfferAction, OfferHistory


def log_offer_history(
    db: Session,
    offer_id: int,
    action: OfferAction,
    user_id: int | None = None,
    notes: str | None = None,
):
    history_entry = OfferHistory(
        offer_id=offer_id, user_id=user_id, action=action, notes=notes
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)
    return history_entry
