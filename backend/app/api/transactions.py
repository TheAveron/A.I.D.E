from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import transaction as crud_transaction
from ..database import User, get_db
from ..schemas import TransactionOut

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=list[TransactionOut], status_code=status.HTTP_200_OK)
def list_transactions(
    faction_id: Optional[int] = None,
    user_id: Optional[int] = None,
    offer_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_transaction.get_transactions(
        db, current_user, faction_id=faction_id, user_id=user_id, offer_id=offer_id
    )
