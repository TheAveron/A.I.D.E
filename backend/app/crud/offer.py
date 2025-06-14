from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import Offer, OfferAction, OfferHistory, OfferStatus
from ..schemas import OfferCreate, OfferUpdate
from .offer_history import log_offer_history


def create_offer(db: Session, offer_data: OfferCreate) -> Offer:
    offer = Offer(**offer_data.dict(), created_at=datetime.utcnow())

    log_offer_history(db, offer.id, OfferAction.CREATED, offer.user_id)  # type: ignore

    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


def get_offer(db: Session, offer_id: int) -> Optional[Offer]:
    return db.query(Offer).filter(Offer.id == offer_id).first()


def list_offers(
    db: Session,
    only_open: bool = True,
    currency: Optional[str] = None,
) -> List[Offer]:
    query = db.query(Offer)

    if only_open:
        query = query.filter(Offer.status == "open")

    if currency:
        query = query.filter(Offer.currency == currency)

    return query.all()


def update_offer_status(
    db: Session, offer_id: int, new_status: OfferStatus
) -> Optional[Offer]:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if offer:
        offer.status = new_status  # type: ignore
        db.commit()
        db.refresh(offer)
    return offer


def update_offer(db: Session, offer_id: int, update_data: OfferUpdate) -> Offer:
    try:
        offer = db.query(Offer).filter(Offer.id == offer_id).first()
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        # Validate update data
        if update_data.price and update_data.price < 0:
            raise HTTPException(status_code=400, detail="Price cannot be negative")

        for key, value in update_data.dict(exclude_unset=True).items():
            setattr(offer, key, value)

        db.commit()
        db.refresh(offer)
        return offer

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def delete_offer(db: Session, offer_id: int) -> bool:
    offer = db.query(Offer).filter(Offer.id == offer_id).first()
    if offer:
        db.delete(offer)
        db.commit()
        return True
    return False


def get_offer_history(db: Session, offer_id: int):
    return (
        db.query(OfferHistory)
        .filter(OfferHistory.offer_id == offer_id)
        .order_by(OfferHistory.timestamp.desc())
        .all()
    )
