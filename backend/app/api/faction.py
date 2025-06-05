from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import faction as faction_crud
from ..database import get_db
from ..schemas import FactionCreate, FactionOut, FactionUpdate

router = APIRouter(
    prefix="/factions",
    tags=["factions"],
)


@router.post("/", response_model=FactionOut, status_code=status.HTTP_201_CREATED)
def create_faction(faction_data: FactionCreate, db: Session = Depends(get_db)):
    # Check unique name
    existing = faction_crud.get_faction_by_name(db, faction_data.name)

    user = get_current_user()

    if existing:
        raise HTTPException(status_code=400, detail="Faction name already exists")
    # Check user already has a faction
    user_faction = faction_crud.get_faction_by_user_id(db, user.id) if user else None  # type: ignore
    if user_faction:
        raise HTTPException(status_code=400, detail="User already belongs to a faction")
    faction = faction_crud.create_faction(db, faction_data)
    return faction


@router.get("/", response_model=List[FactionOut])
def list_factions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return faction_crud.list_factions(db, skip=skip, limit=limit)


@router.get("/{faction_id}", response_model=FactionOut)
def get_faction(faction_id: int, db: Session = Depends(get_db)):
    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    return faction


@router.put("/{faction_id}", response_model=FactionOut)
def update_faction(
    faction_id: int, faction_update: FactionUpdate, db: Session = Depends(get_db)
):
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


@router.delete("/{faction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faction(faction_id: int, db: Session = Depends(get_db)):
    faction = faction_crud.get_faction(db, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    faction_crud.delete_faction(db, faction)
    return None
