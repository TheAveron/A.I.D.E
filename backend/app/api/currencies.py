from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_user
from backend.app.database.models.user import User

from ..database import get_db

from ..crud import currencies as crud_currencies
from ..schemas import CurrencyOut, CurrencyCreate, CurrencyUpdate
from ..misc import FactionPermission, check_faction_permission

router = APIRouter(prefix="/currencies", tags=["currencies"])


@router.post("/", response_model=CurrencyOut, status_code=status.HTTP_201_CREATED)
def create_currency(
    currency_in: CurrencyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Check faction permission
    check_faction_permission(current_user, FactionPermission.MANAGE_FUNDS)

    existing = crud_currencies.get_currency(db, currency_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Currency already exists"
        )

    return crud_currencies.create_currency(db, currency_in)


@router.put("/{currency_name}", response_model=CurrencyOut)
def update_currency(
    currency_name: str,
    currency_in: CurrencyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_faction_permission(current_user, FactionPermission.MANAGE_FUNDS)
    return crud_currencies.update_currency(db, currency_name, currency_in)


@router.delete("/{currency_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_currency(
    currency_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_faction_permission(current_user, FactionPermission.MANAGE_FUNDS)
    crud_currencies.delete_currency(db, currency_name)
    return None
