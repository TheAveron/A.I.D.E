from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_user
from backend.app.database.models.user import User

from ..crud import currencies as crud_currencies
from ..database import get_db
from ..misc import FactionPermission, check_faction_permission
from ..schemas import CurrencyCreate, CurrencyOut, CurrencyUpdate

router = APIRouter(prefix="/currencies", tags=["currencies"])


@router.post("/create", response_model=CurrencyOut, status_code=status.HTTP_201_CREATED)
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


@router.get("/{currency_name}", response_model=CurrencyOut)
def get_currency(
    currency_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    currency = crud_currencies.get_currency(db, currency_name)
    if not currency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Currency not found"
        )

    if currency.faction_id != current_user.faction_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own faction's currency",
        )

    if not (
        current_user.role
        and current_user.role.has_permission(FactionPermission.MANAGE_FUNDS)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission to view faction currency information",
        )

    return currency


@router.put("/{currency_name}/update", response_model=CurrencyOut)
def update_currency(
    currency_name: str,
    currency_in: CurrencyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_faction_permission(current_user, FactionPermission.MANAGE_FUNDS)
    return crud_currencies.update_currency(db, currency_name, currency_in)


@router.delete("/{currency_name}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_currency(
    currency_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    check_faction_permission(current_user, FactionPermission.MANAGE_FUNDS)
    crud_currencies.delete_currency(db, currency_name)
    return None
