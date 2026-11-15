import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..crud import get_faction
from ..database import Currency, Faction, Offer, OfferHistory, Role, Transaction, User
from ..database.clock import utcnow
from ..misc import FactionPermission, OfferAction, OfferStatus, OfferType
from ..schemas import OfferAccept, OfferCreate, OfferUpdate
from .notification import members_with_permission, notify_many
from .offer_history import create_offer_history

logger = logging.getLogger("aide")


def get_offer(db: Session, offer_id: int) -> Optional[Offer]:
    return db.query(Offer).filter(Offer.offer_id == offer_id).first()


def _clean_ids(ids: Optional[list[int]]) -> Optional[list[int]]:
    """The ids once each, in order; an empty list means "nobody listed"."""
    if not ids:
        return None
    return list(dict.fromkeys(ids))


def check_allowed_parties(
    db: Session, users: Optional[list[int]], factions: Optional[list[int]]
):
    """Refuse ids that belong to nobody (a typo would make a ghost offer)."""
    if users:
        known = {u for (u,) in db.query(User.user_id).filter(User.user_id.in_(users))}
        missing = sorted(set(users) - known)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown user id: {missing[0]}",
            )
    if factions:
        known = {
            f
            for (f,) in db.query(Faction.faction_id).filter(
                Faction.faction_id.in_(factions)
            )
        }
        missing = sorted(set(factions) - known)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown faction id: {missing[0]}",
            )


def can_view_offer(offer: Offer, viewer: Optional[User]) -> bool:
    """Whether `viewer` (None: not logged in) may see and accept `offer`.

    A public offer is for everybody. A private one is for its owner (or, for
    a faction's offer, the faction's members), the listed users and the
    members of the listed factions - and for admins.
    """
    if not offer.is_private:
        return True
    if viewer is None:
        return False
    if viewer.is_admin:
        return True
    if offer.user_id is not None and offer.user_id == viewer.user_id:
        return True
    if viewer.faction_id is not None and viewer.faction_id in (
        offer.faction_id,
        *(offer.allowed_faction_ids or ()),
    ):
        return True
    return viewer.user_id in (offer.allowed_user_ids or ())


def get_offers(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[OfferStatus] = None,
    currency: Optional[str] = None,
    user_id: Optional[int] = None,
    faction_id: Optional[int] = None,
    offer_type: Optional[OfferType] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    viewer: Optional[User] = None,
) -> list[Offer]:
    """Offers `viewer` may see, newest first (offer_id breaks ties)."""
    query = db.query(Offer)
    if viewer is None or not viewer.is_admin:
        # Private offers are few: the ones this viewer may see are picked in
        # Python, the rest of the filtering and the paging stay in SQL.
        visible_private = [
            o.offer_id
            for o in db.query(Offer).filter(Offer.is_private.is_(True))
            if can_view_offer(o, viewer)
        ]
        query = query.filter(
            or_(Offer.is_private.is_(False), Offer.offer_id.in_(visible_private))
        )
    if status:
        query = query.filter(Offer.status == status)

    if currency:
        query = query.filter(Offer.currency_name == currency)

    if user_id is not None:
        query = query.filter(Offer.user_id == user_id)

    if faction_id is not None:
        query = query.filter(Offer.faction_id == faction_id)

    if offer_type:
        query = query.filter(Offer.offer_type == offer_type)

    if search and search.strip():
        # "%" and "_" typed by the user are plain characters here, not wildcards
        escaped = (
            search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        query = query.filter(Offer.item_description.ilike(f"%{escaped}%", escape="\\"))

    if min_price is not None:
        query = query.filter(Offer.price_per_unit >= min_price)

    if max_price is not None:
        query = query.filter(Offer.price_per_unit <= max_price)

    return (
        query.order_by(Offer.created_at.desc(), Offer.offer_id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


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
    data["allowed_user_ids"] = _clean_ids(offer_in.allowed_user_ids)
    data["allowed_faction_ids"] = _clean_ids(offer_in.allowed_faction_ids)
    check_allowed_parties(db, data["allowed_user_ids"], data["allowed_faction_ids"])
    data["is_private"] = bool(data["allowed_user_ids"] or data["allowed_faction_ids"])

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

    changes = offer_update.model_dump(exclude_unset=True)

    new_status = changes.get("status")
    if new_status is not None and new_status != OfferStatus.CANCELLED:
        raise HTTPException(
            status_code=400, detail="An offer can only be moved to CANCELLED"
        )

    for field in ("allowed_user_ids", "allowed_faction_ids"):
        if field in changes:
            changes[field] = _clean_ids(changes[field])
    if "allowed_user_ids" in changes or "allowed_faction_ids" in changes:
        check_allowed_parties(
            db,
            changes.get("allowed_user_ids"),
            changes.get("allowed_faction_ids"),
        )

    try:
        for field, value in changes.items():
            setattr(offer, field, value)
        offer.is_private = bool(offer.allowed_user_ids or offer.allowed_faction_ids)
        offer.updated_at = utcnow()

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
    offer = db.query(Offer).filter(Offer.offer_id == offer_id).with_for_update().first()

    # A private offer doesn't exist for those it isn't addressed to.
    if not offer or not can_view_offer(offer, current_user):
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
        timestamp=utcnow(),
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

    # The owner hears about it: the user, or the members who run the
    # faction's offers.
    owners = (
        [offer.user_id]
        if offer.user_id is not None
        else members_with_permission(
            db, offer.faction_id, FactionPermission.CREATE_OFFERS
        )
    )
    notify_many(
        db,
        [u for u in owners if u != current_user.user_id],
        "offer_accepted",
        f"{buyer} a accepté votre offre « {offer.item_description} » "
        f"({quantity} × {offer.price_per_unit} {offer.currency_name})",
        "/transactions",
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
