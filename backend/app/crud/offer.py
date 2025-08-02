from datetime import datetime
from typing import Optional
from uu import Error

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.crud.faction import get_faction
from backend.app.crud.user import get_user_by_id

from ..database import Offer, OfferHistory, Role, Transaction, User
from ..misc import OfferAction, OfferStatus
from ..schemas import OfferAccept, OfferCreate, OfferUpdate
from .offer_history import create_offer_history


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
    offer = Offer(
        **offer_in.dict(exclude_unset=True),
        status=OfferStatus.OPEN,
    )
    db.add(offer)
    try:
        db.commit()
        db.refresh(offer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid offer: check constraints violated.",
        )

    # Log creation
    create_offer_history(
        db=db,
        offer_id=offer.offer_id,
        actor_user_id=offer.user_id,
        actor_faction_id=offer.faction_id,
        action=OfferAction.CREATED,
        notes="Offer created",
    )

    return offer


# ----- UPDATE -----
def update_offer(
    db: Session,
    offer_id: int,
    offer_update: OfferUpdate,
    actor_user_id: Optional[int] = None,
    actor_faction_id: Optional[int] = None,
) -> Optional[Offer]:
    try:
        offer = get_offer(db, offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")

        for field, value in offer_update.dict(exclude_unset=True).items():
            setattr(offer, field, value)

        offer.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(offer)

        # Log update
        create_offer_history(
            db=db,
            offer_id=offer.offer_id,
            actor_user_id=actor_user_id,
            actor_faction_id=actor_faction_id,
            action=OfferAction.UPDATED,
            notes="Offer updated",
        )

        return offer

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


def get_offer_history(db: Session, offer_id: int):
    return (
        db.query(OfferHistory)
        .filter(OfferHistory.offer_id == offer_id)
        .order_by(OfferHistory.timestamp.desc())
        .all()
    )


def accept_offer(db: Session, current_user: User, offer_id: int, request: OfferAccept):
    # --- Fetch offer ---
    offer = db.query(Offer).filter(Offer.offer_id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    # --- Check if offer is open ---
    if offer.status != OfferStatus.OPEN:
        raise HTTPException(status_code=400, detail="Offer is not available")

    buyer = str()

    # --- Validate buy_for parameter ---
    if request.buyer_faction_id:
        # Prevent self-purchase
        if offer.user_id == current_user.user_id:
            raise HTTPException(
                status_code=403, detail="You can't accept your own offer"
            )
        buyer_identity = {"buyer_user_id": current_user.user_id}

        buyer = current_user.username

    elif request.buyer_faction_id:
        # User must be in a faction
        if not current_user.faction_id:
            raise HTTPException(status_code=403, detail="You don't belong to a faction")

        # Prevent self-purchase for faction
        if offer.faction_id == current_user.faction_id:
            raise HTTPException(
                status_code=403, detail="You can't accept your own faction's offer"
            )

        # Check if user has permission in their faction
        role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
        if not role or role.name.lower() not in {"chief", "treasurer", "merchant"}:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to accept offers for your faction",
            )

        buyer_identity = {"buyer_faction_id": current_user.faction_id}

        faction = get_faction(db, current_user.faction_id)
        if faction:
            buyer = faction.name
        else:
            raise Error(
                "No faction with this ID, this souldn't happen, so contact the dev please"
            )

    else:
        raise HTTPException(
            status_code=400, detail="buy_for must be 'user' or 'faction'"
        )

    # --- Handle quantity ---
    if request.quantity is None:
        request.quantity = offer.quantity

    if request.quantity > offer.quantity:
        raise HTTPException(
            status_code=400, detail="Not enough quantity available for this offer"
        )

    # --- Create transaction ---
    transaction = Transaction(
        offer_id=offer.offer_id,
        amount=request.quantity * offer.price_per_unit,
        currency_name=offer.currency_name,
        timestamp=datetime.utcnow(),
        **buyer_identity,
    )
    db.add(transaction)

    # --- Update offer quantity or close offer ---
    offer.quantity -= request.quantity
    if offer.quantity <= 0:
        offer.status = OfferStatus.CLOSED
        offer.accepted_by_user_id = (
            buyer_identity.get("buyer_user_id")
            if "buyer_user_id" in buyer_identity
            else None
        )
        offer.accepted_by_faction_id = (
            buyer_identity.get("buyer_faction_id")
            if "buyer_faction_id" in buyer_identity
            else None
        )

    create_offer_history(
        db,
        offer.offer_id,
        OfferAction.ACCEPTED,
        current_user.user_id,
        notes=f"Accepted by {buyer} (quantity: {request.quantity})",
    )

    db.commit()
    db.refresh(offer)
    db.refresh(transaction)

    return {
        "message": "Offer accepted successfully",
        "offer": offer,
        "transaction": transaction,
    }
