from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import offer as offer_crud
from ..database import get_db
from ..enums import OfferStatus
from ..schemas import OfferAccept, OfferCreate, OfferOut, OfferUpdate

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("/", response_model=list[OfferOut])
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
def create_offer(offer_in: OfferCreate, db: Session = Depends(get_db)):
    return offer_crud.create_offer(db, offer_in)


@router.get("/{offer_id}", response_model=OfferOut)
def get_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = offer_crud.get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@router.put("/{offer_id}/update", response_model=OfferOut)
def modify_offer(
    offer_id: int, update_data: OfferUpdate, db: Session = Depends(get_db)
):
    updated = offer_crud.update_offer(db, offer_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Offer not found")
    return updated


@router.delete("/{offer_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def remove_offer(offer_id: int, db: Session = Depends(get_db)):
    deleted = offer_crud.update_offer(
        db, offer_id, OfferUpdate(status=OfferStatus.CANCELLED)
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Offer not found")
    return


@router.post("/{offer_id}/accept", response_model=OfferOut)
def accept_offer(
    offer_id: int,
    acceptance: OfferAccept,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return offer_crud.accept_offer(db, current_user, offer_id, acceptance)
