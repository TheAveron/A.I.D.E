from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import faction as faction_crud
from ..database import get_db
from ..misc import FactionPermission, check_faction_permission
from ..schemas import FactionCreate, FactionOut, FactionUpdate

router = APIRouter(
    prefix="/factions",
    tags=["factions"],
)


@router.post("/create", response_model=FactionOut, status_code=status.HTTP_201_CREATED)
def create_faction(
    faction_data: FactionCreate, db: Session = Depends(get_db)
) -> FactionOut:
    """
    Create a new faction.

    Parameters:
    - faction: Faction data including name

    Returns:
    - FactionOut: Created faction data

    Raises:
    - 400: Faction already exists
    - 422: Invalid faction data
    """
    user = get_current_user()
    user_faction = (
        faction_crud.get_faction_by_user_id(db, user.user_id) if user else None
    )

    if user_faction:
        raise HTTPException(status_code=400, detail="User already belongs to a faction")

    if faction_crud.get_faction_by_name(db, faction_data.name):
        raise HTTPException(status_code=400, detail="Faction name already exists")

    return faction_crud.create_faction(db, faction_data)


@router.get("/list", response_model=list[FactionOut], status_code=status.HTTP_200_OK)
def list_factions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return faction_crud.list_factions(db, skip=skip, limit=limit)


@router.get("/{faction_id}", response_model=FactionOut, status_code=status.HTTP_200_OK)
def get_faction(faction_id: int, db: Session = Depends(get_db)):
    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    return faction


@router.put(
    "/{faction_id}/update",
    response_model=FactionOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def update_faction(
    faction_id: int,
    faction_update: FactionUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Require permission to manage roles or handle members
    check_faction_permission(current_user, FactionPermission.MANAGE_ROLES)

    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")

    try:
        updated_faction = faction_crud.update_faction_validation(
            db, faction, faction_update
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return updated_faction


@router.delete("/{faction_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_faction(
    faction_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Only allow deletion if the user can manage roles (or you can make this a different strict permission)
    check_faction_permission(current_user, FactionPermission.MANAGE_ROLES)

    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")

    faction_crud.delete_faction(db, faction)
    return None
