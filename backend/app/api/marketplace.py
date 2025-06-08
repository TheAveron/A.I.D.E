from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import fulfill_offer, get_offer, log_offer_history
from ..database import Offer, OfferAction, OfferStatus, Role, User, get_db
from ..schemas import OfferOut, TransactionOut

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.post("/offers/{offer_id}/accept", response_model=OfferOut)
def accept_offer(
    offer_id: int,
    buy_for: str = "user",  # either "user" or "faction"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offer = get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    if offer.status != OfferStatus.OPEN:  # type: ignore
        raise HTTPException(status_code=400, detail="Offer is not available")

    if buy_for not in {"user", "faction"}:
        raise HTTPException(
            status_code=400, detail="buy_for must be 'user' or 'faction'"
        )

    # Handle personal purchase
    if buy_for == "user":
        # You can't accept your own offer
        if offer.user_id == current_user.id:  # type: ignore
            raise HTTPException(
                status_code=403, detail="You can't accept your own offer"
            )
        buyer_identity = {"user_id": current_user.id}

    # Handle faction purchase
    elif buy_for == "faction":
        if not current_user.faction_id:  # type: ignore
            raise HTTPException(status_code=403, detail="You don't belong to a faction")
        if offer.faction_id == current_user.faction_id:  # type: ignore
            raise HTTPException(
                status_code=403, detail="You can't accept your own faction's offer"
            )

        # Check permission
        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        if not role or role.name.lower() not in {"chief", "treasurer", "merchant"}:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to accept offers for your faction",
            )

        buyer_identity = {"faction_id": current_user.faction_id}

    # Fulfill the offer
    try:
        fulfilled_offer = fulfill_offer(
            db=db,
            offer=offer,
            buyer=current_user,
            target=buyer_identity,  # who is receiving the item / paying # type: ignore
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fulfill offer: {str(e)}"
        )

    log_offer_history(db, offer.id, OfferAction.ACCEPTED, user_id=current_user.id)  # type: ignore
    return fulfilled_offer


@router.post("/offers/{offer_id}/decline", response_model=OfferOut)
def decline_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offer = get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Check if the user personally created the offer
    if offer.user_id == current_user.id:  # type: ignore
        authorized = True

    # Check if the offer was created by the user's faction and user has permission
    elif offer.faction_id == current_user.faction_id:  # type: ignore
        role = db.query(Role).filter(Role.id == current_user.role_id).first()
        authorized_roles = {"chief", "treasurer", "merchant", "logistics"}
        authorized = role and role.name.lower() in authorized_roles

    else:
        authorized = False

    if not authorized:
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this offer"
        )

    offer.status = OfferStatus.CANCELLED  # type: ignore
    log_offer_history(db, offer.id, OfferAction.CANCELLED, current_user.id)  # type: ignore

    db.commit()
    db.refresh(offer)
    return offer
