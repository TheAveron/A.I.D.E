from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..crud import offer_history as offer_history_crud
from ..database import get_db
from ..schemas import OfferHistoryOut

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/", response_model=list[OfferHistoryOut])
def list_offer_histories(
    actor_user_id: Optional[int] = None,
    actor_faction_id: Optional[int] = None,
    offer_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return offer_history_crud.get_offer_histories(
        db=db,
        actor_user_id=actor_user_id,
        actor_faction_id=actor_faction_id,
        offer_id=offer_id,
        skip=skip,
        limit=limit,
    )
