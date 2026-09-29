from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import offer as offer_crud
from ..database import Offer, User, get_db
from ..misc import FactionPermission, OfferStatus, check_faction_permission
from ..schemas import (OfferAccept, OfferAcceptOut, OfferCreate, OfferOut,
                       OfferUpdate)

router = APIRouter(prefix="/offers", tags=["Offers"])


def _offer_manager(current_user: User, offer: Offer) -> dict:
    """Check that `current_user` may modify/cancel `offer` and return the
    matching history actor.

    A personal offer belongs to its creator. A faction's offer is managed by
    members of that faction whose role allows creating offers. The history
    table wants exactly one actor, hence the two shapes.
    """
    if offer.user_id is not None:
        if offer.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage your own offers",
            )
        return {"actor_user_id": current_user.user_id}

    check_faction_permission(
        current_user, FactionPermission.CREATE_OFFERS, target_faction_id=offer.faction_id
    )
    return {"actor_faction_id": offer.faction_id}


@router.get("/list", response_model=list[OfferOut], status_code=status.HTTP_200_OK)
def list_offers(
    status: Optional[OfferStatus] = Query(None),
    currency: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return offer_crud.get_offers(
        db, status=status, skip=skip, limit=limit, currency=currency
    )


@router.post("/create", response_model=OfferOut, status_code=status.HTTP_201_CREATED)
def create_offer(
    offer_in: OfferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (offer_in.user_id is None) == (offer_in.faction_id is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one of 'user_id' or 'faction_id' must be provided",
        )

    if offer_in.faction_id is not None:
        check_faction_permission(
            current_user,
            FactionPermission.CREATE_OFFERS,
            target_faction_id=offer_in.faction_id,
        )
    elif offer_in.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create offers in your own name",
        )

    return offer_crud.create_offer(db, offer_in)


@router.get("/detail/{offer_id}", response_model=OfferOut)
def get_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = offer_crud.get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@router.put(
    "/update/{offer_id}", response_model=OfferOut, status_code=status.HTTP_202_ACCEPTED
)
def modify_offer(
    offer_id: int,
    update_data: OfferUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offer = offer_crud.get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    return offer_crud.update_offer(
        db,
        offer_id,
        update_data,
        actor_name=current_user.username,
        **_offer_manager(current_user, offer),
    )


@router.delete("/delete/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_offer(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offer = offer_crud.get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    offer_crud.update_offer(
        db,
        offer_id,
        OfferUpdate(status=OfferStatus.CANCELLED),
        actor_name=current_user.username,
        **_offer_manager(current_user, offer),
    )


@router.post(
    "/accept/{offer_id}",
    response_model=OfferAcceptOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def accept_offer(
    offer_id: int,
    acceptance: OfferAccept,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return offer_crud.accept_offer(db, current_user, offer_id, acceptance)
