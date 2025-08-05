from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import get_offer, update_offer
from ..database import Role, User, get_db
from ..schemas import OfferOut, OfferStatus, OfferUpdate

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.post("/offers/{offer_id}/decline", response_model=OfferOut, deprecated=True)
def decline_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return
    offer = get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Check if the user personally created the offer
    if offer.user_id == current_user.user_id:
        authorized = True

    # Check if the offer was created by the user's faction and user has permission
    elif offer.faction_id == current_user.faction_id:
        role = db.query(Role).filter(Role.role_id == current_user.role_id).first()
        authorized_roles = {"chief", "treasurer", "merchant", "logistics"}
        authorized = role and role.name.lower() in authorized_roles

    else:
        authorized = False

    if not authorized:
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this offer"
        )

    update_offer(
        db,
        offer.offer_id,
        OfferUpdate(status=OfferStatus.CANCELLED),
        current_user.user_id,
    )

    db.commit()
    db.refresh(offer)
    return offer
