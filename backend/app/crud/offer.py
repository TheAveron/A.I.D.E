import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..crud import get_faction
from ..database import (Currency, Offer, OfferHistory, Role, Transaction,
                        User)
from ..misc import OfferAction, OfferStatus
from ..schemas import OfferAccept, OfferCreate, OfferUpdate
from .offer_history import create_offer_history

logger = logging.getLogger("aide")


def get_offer(db: Session, offer_id: int) -> Optional[Offer]:
    return db.query(Offer).filter(Offer.offer_id == offer_id).first()


def get_offers(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[OfferStatus] = None,
    currency: Optional[str] = None,
) -> list[Offer]:
    query = db.query(Offer)
    if status:
        query = query.filter(Offer.status == status)

    if currency:
        query = query.filter(Offer.currency_name == currency)

    return query.offset(skip).limit(limit).all()


def create_offer(db: Session, offer_in: OfferCreate) -> Offer:
    """Create an OPEN offer.

    Ownership (user_id / faction_id) must already have been checked by the
    caller. `init_quantity` is always derived from `quantity` here: it is the
    record of the original amount, not something a client gets to choose.
    """
    if not db.query(Currency).filter(Currency.name == offer_in.currency_name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown currency: {offer_in.currency_name}",
        )

    data = offer_in.model_dump()
    data["init_quantity"] = offer_in.quantity

    offer = Offer(**data, status=OfferStatus.OPEN)
    db.add(offer)
    try:
        db.flush()  # assigns offer_id and checks the DB constraints
        create_offer_history(
            db=db,
            offer_id=offer.offer_id,
            actor_user_id=offer.user_id,
            actor_faction_id=offer.faction_id,
            action=OfferAction.CREATED,
            notes="Offer created",
            commit=False,
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid offer: check constraints violated.",
        )

    db.refresh(offer)
    return offer


def update_offer(
    db: Session,
    offer_id: int,
    offer_update: OfferUpdate,
    actor_user_id: Optional[int] = None,
    actor_faction_id: Optional[int] = None,
    actor_name: Optional[str] = None,
) -> Optional[Offer]:
    """Modify or cancel an OPEN offer, recording who did it.

    Exactly one of `actor_user_id` / `actor_faction_id` must be given (the
    history table enforces it). The change and its history entry are written
    in one transaction.
    """
    offer = get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.status != OfferStatus.OPEN:
        raise HTTPException(
            status_code=400, detail="Only open offers can be modified or cancelled"
        )

    changes = offer_update.dict(exclude_unset=True)

    new_status = changes.get("status")
    if new_status is not None and new_status != OfferStatus.CANCELLED:
        raise HTTPException(
            status_code=400, detail="An offer can only be moved to CANCELLED"
        )

    try:
        for field, value in changes.items():
            setattr(offer, field, value)
        offer.updated_at = datetime.utcnow()

        cancelled = new_status == OfferStatus.CANCELLED
        who = f" by {actor_name}" if actor_name else ""
        create_offer_history(
            db=db,
            offer_id=offer.offer_id,
            actor_user_id=actor_user_id,
            actor_faction_id=actor_faction_id,
            action=OfferAction.CANCELLED if cancelled else OfferAction.UPDATED,
            notes=f"Offer {'cancelled' if cancelled else 'updated'}{who}",
            commit=False,
        )
        db.commit()
        db.refresh(offer)
        return offer

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while updating offer %s", offer_id)
        raise HTTPException(status_code=500, detail="Database error")


def get_offer_history(db: Session, offer_id: int):
    return (
        db.query(OfferHistory)
        .filter(OfferHistory.offer_id == offer_id)
        .order_by(OfferHistory.timestamp.desc())
        .all()
    )


def accept_offer(db: Session, current_user: User, offer_id: int, request: OfferAccept):
    # Row lock: two simultaneous buyers must not both pass the quantity check
    # below and oversell the offer (no-op on SQLite, real on PostgreSQL).
    offer = (
        db.query(Offer).filter(Offer.offer_id == offer_id).with_for_update().first()
    )

    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.status != OfferStatus.OPEN:
        raise HTTPException(status_code=400, detail="Offer is not available")

    buyer_identity = {}
    buyer = ""
    history_actor = {}

    if request.buyer_user_id:
        if offer.user_id == current_user.user_id:
            raise HTTPException(
                status_code=403, detail="You can't accept your own offer"
            )
        buyer_identity = {"buyer_user_id": current_user.user_id}
        buyer = current_user.username
        history_actor = {"actor_user_id": current_user.user_id}

    elif request.buyer_faction_id:
        if not current_user.faction_id:
            raise HTTPException(status_code=403, detail="You don't belong to a faction")

        if offer.faction_id == current_user.faction_id:
            raise HTTPException(
                status_code=403, detail="You can't accept your own faction's offer"
            )

        role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
        if (
            not role
            or role.faction_id != current_user.faction_id
            or not role.accept_offers
        ):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to accept offers for your faction",
            )

        buyer_identity = {"buyer_faction_id": current_user.faction_id}

        faction = get_faction(db, current_user.faction_id)
        if faction:
            buyer = f"{faction.name} (via {current_user.username})"
        else:
            raise RuntimeError(
                "No faction with this ID. This shouldn't happen, contact dev."
            )
        # A faction's history is filtered by actor_faction_id in the UI.
        history_actor = {"actor_faction_id": current_user.faction_id}

    else:
        raise HTTPException(
            status_code=400,
            detail="One of 'buyer_user_id' or 'buyer_faction_id' must be provided",
        )

    quantity = request.quantity if request.quantity is not None else offer.quantity

    if quantity > offer.quantity:
        raise HTTPException(
            status_code=400, detail="Not enough quantity available for this offer"
        )

    transaction = Transaction(
        offer_id=offer.offer_id,
        amount=quantity * offer.price_per_unit,
        currency_name=offer.currency_name,
        timestamp=datetime.utcnow(),
        **buyer_identity,
    )
    db.add(transaction)

    offer.quantity -= quantity
    if offer.quantity <= 0:
        offer.status = OfferStatus.CLOSED
        offer.accepted_by_user_id = buyer_identity.get("buyer_user_id")
        offer.accepted_by_faction_id = buyer_identity.get("buyer_faction_id")

    create_offer_history(
        db,
        offer.offer_id,
        OfferAction.ACCEPTED,
        notes=f"Accepted by {buyer} (quantity: {quantity})",
        commit=False,
        **history_actor,
    )

    db.commit()
    db.refresh(offer)
    db.refresh(transaction)

    # Shape expected by OfferAcceptOut (the route's response_model).
    return {
        "offer_id": offer.offer_id,
        "transaction_id": transaction.transaction_id,
        "status": offer.status.value,
    }
