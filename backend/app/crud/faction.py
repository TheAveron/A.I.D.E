from typing import List, Optional

from sqlalchemy.orm import Session

from ..database import Faction, User
from ..schemas import FactionCreate, FactionUpdate


def get_faction(db: Session, faction_id: int) -> Optional[Faction]:
    return db.query(Faction).filter(Faction.id == faction_id).first()


def get_faction_by_name(db: Session, name: str) -> Optional[Faction]:
    return db.query(Faction).filter(Faction.name == name).first()


def get_faction_by_user_id(db: Session, user_id: int) -> Optional[Faction]:
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.faction_id:  # type: ignore
        return db.query(Faction).filter(Faction.id == user.faction_id).first()
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
) -> Faction:
    # Example validation: check if new name is unique if changing
    if faction_update.name and faction_update.name != faction.name:
        existing = get_faction_by_name(db, faction_update.name)
        if existing and existing.id != faction.id:  # type: ignore
            raise ValueError("Faction name already exists")

    # Apply updates if no errors
    if faction_update.name is not None:
        faction.name = faction_update.name  # type: ignore
    if faction_update.description is not None:
        faction.description = faction_update.description  # type: ignore
    if faction_update.currency_amount is not None:
        faction.currency_amount = faction_update.currency_amount  # type: ignore

    db.commit()
    db.refresh(faction)
    return faction


def delete_faction(db: Session, faction: Faction) -> None:
    db.delete(faction)
    db.commit()
