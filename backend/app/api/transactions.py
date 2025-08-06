from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..crud import transaction as crud_transaction
from ..database import get_db
from ..schemas import TransactionOut

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=list[TransactionOut], status_code=status.HTTP_200_OK)
def list_transactions(
    faction_id: Optional[int] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return crud_transaction.get_transactions(db, faction_id, user_id)
