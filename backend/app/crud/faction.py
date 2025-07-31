from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import Faction, User
from ..schemas import FactionCreate, FactionUpdate


def get_faction(db: Session, faction_id: int) -> Optional[Faction]:
    return db.query(Faction).filter(Faction.faction_id == faction_id).first()


def get_faction_by_name(db: Session, name: str) -> Optional[Faction]:
    return db.query(Faction).filter(Faction.name == name).first()


def get_faction_by_user_id(db: Session, user_id: int) -> Optional[Faction]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user and user.faction_id:  # type: ignore
        return db.query(Faction).filter(Faction.faction_id == user.faction_id).first()
    return None


def list_factions(db: Session, skip: int = 0, limit: int = 100) -> List[Faction]:
    return db.query(Faction).offset(skip).limit(limit).all()


def create_faction(db: Session, faction_data: FactionCreate) -> Faction:
    faction = Faction(
        name=faction_data.name,
        description=faction_data.description,
        currency_amount=faction_data.currency_amount,
    )
    db.add(faction)
    db.commit()
    db.refresh(faction)
    return faction


def update_faction_validation(
    db: Session, faction: Faction, faction_update: FactionUpdate
):
    try:
        for key, value in faction_update.dict(exclude_unset=True).items():
            setattr(faction, key, value)
        db.commit()
        db.refresh(faction)
        return faction
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Database error occurred: {str(e)}"
        )


def delete_faction(db: Session, faction: Faction) -> None:
    db.delete(faction)
    db.commit()
