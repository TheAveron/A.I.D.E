from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import offer_history as offer_history_crud
from ..database import User, get_db
from ..schemas import OfferHistoryOut

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=list[OfferHistoryOut])
def list_offer_histories(
    actor_user_id: Optional[int] = None,
    actor_faction_id: Optional[int] = None,
    offer_id: Optional[int] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return offer_history_crud.get_offer_histories(
        db=db,
        viewer=current_user,
        actor_user_id=actor_user_id,
        actor_faction_id=actor_faction_id,
        offer_id=offer_id,
        skip=skip,
        limit=limit,
    )
