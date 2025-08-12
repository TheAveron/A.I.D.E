from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import currencies as crud_currencies
from ..database import User, get_db
from ..schemas import CurrencyCreate, CurrencyOut, CurrencyUpdate

router = APIRouter(prefix="/currencies", tags=["Currencies"])


@router.post("/create", response_model=CurrencyOut, status_code=status.HTTP_201_CREATED)
def create_currency(
    currency_in: CurrencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (current_user.role and current_user.role.manage_funds):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission to create faction currency",
        )
    existing = crud_currencies.get_currency(db, currency_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Currency already exists"
        )

    return crud_currencies.create_currency(db, currency_in)


@router.get(
    "/faction/{faction_id}",
    response_model=CurrencyOut | None,
    status_code=status.HTTP_200_OK,
)
def get_currency_by_faction(
    faction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    currency = crud_currencies.get_currency_by_faction(db, faction_id)

    if not currency:
        return None

    return currency


@router.get(
    "/detail/{currency_name}",
    response_model=CurrencyOut,
    status_code=status.HTTP_200_OK,
)
def get_currency_by_name(
    currency_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    if not (current_user.role and current_user.role.manage_funds):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission to view faction currency information",
        )

    return currency


@router.put(
    "/update/{currency_name}",
    response_model=CurrencyOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def update_currency(
    currency_name: str,
    currency_in: CurrencyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not (current_user.role and current_user.role.manage_funds):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission to update faction currency information",
        )
    return crud_currencies.update_currency(db, currency_name, currency_in)


@router.delete("/delete/{currency_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_currency(
    currency_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (current_user.role and current_user.role.manage_funds):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You lack permission to delete faction currency",
        )
    crud_currencies.delete_currency(db, currency_name)
    return None
