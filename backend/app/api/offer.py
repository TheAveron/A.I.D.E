from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core import get_current_user
from crud import (
    create_offer,
    delete_offer,
    get_offer,
    get_offer_history,
    list_offers,
    update_offer,
    update_offer_status,
)
from database import User, get_db
from schemas import OfferCreate, OfferHistoryOut, OfferOut, OfferUpdate

router = APIRouter(prefix="/offers", tags=["marketplace"])


@router.post("/create", response_model=OfferOut, status_code=status.HTTP_201_CREATED)
def create_new_offer(offer: OfferCreate, db: Session = Depends(get_db)):
    return create_offer(db, offer)


@router.get("/{offer_id}", response_model=OfferOut)
def read_offer(offer_id: int, db: Session = Depends(get_db)):
    db_offer = get_offer(db, offer_id)
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return db_offer


@router.get("/list", response_model=List[OfferOut])
def read_offers(
    only_open: bool = True,
    currency: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return list_offers(db, only_open=only_open, currency=currency)


@router.patch("/{offer_id}/status", response_model=OfferOut)
def change_offer_status(offer_id: int, status: str, db: Session = Depends(get_db)):
    updated_offer = update_offer_status(db, offer_id, status)  # type: ignore
    if not updated_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return updated_offer


@router.put("/{offer_id}", response_model=OfferOut)
def modify_offer(
    offer_id: int, update_data: OfferUpdate, db: Session = Depends(get_db)
):
    updated = update_offer(db, offer_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Offer not found")
    return updated


@router.delete("/{offer_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def remove_offer(offer_id: int, db: Session = Depends(get_db)):
    deleted = delete_offer(db, offer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Offer not found")
    return


@router.get("/{offer_id}/history", response_model=List[OfferHistoryOut])
def read_offer_history(
    offer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offer = get_offer(db, offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    # Optionally, you can add permission checks here if needed
    # e.g. only creators or faction members can see history

    history = get_offer_history(db, offer_id)
    return history
