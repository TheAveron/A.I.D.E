import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import Faction, User
from ..schemas import FactionCreate, FactionUpdate
from .documents import normalize
from .faction_role import create_default_faction_roles

logger = logging.getLogger("aide")


def get_faction(db: Session, faction_id: int) -> Optional[Faction]:
    return db.query(Faction).filter(Faction.faction_id == faction_id).first()


def get_faction_by_name(db: Session, name: str) -> Optional[Faction]:
    return db.query(Faction).filter(Faction.name == name).first()


def get_faction_by_user_id(db: Session, user_id: int) -> Optional[Faction]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user and user.faction_id:
        return db.query(Faction).filter(Faction.faction_id == user.faction_id).first()
    return None


def normalized_name_taken(
    db: Session, name: str, exclude_faction_id: Optional[int] = None
) -> bool:
    """Whether another faction's name maps to the same documents folder.

    Faction documents live in a folder named after `normalize(name)`, which
    drops case, digits and punctuation ("Team 1" and "Team 2" both become
    "team"). Two such factions would share - and overwrite - each other's
    documents, so their names are treated as identical.
    """
    key = normalize(name)
    for faction_id, existing in db.query(Faction.faction_id, Faction.name):
        if faction_id != exclude_faction_id and normalize(existing) == key:
            return True
    return False


def list_factions(db: Session, skip: int = 0, limit: int = 100) -> list[Faction]:
    return db.query(Faction).offset(skip).limit(limit).all()


def create_faction(db: Session, faction_data: FactionCreate, user_id: int) -> Faction:
    faction = Faction(
        name=faction_data.name,
        description=faction_data.description,
    )
    db.add(faction)
    db.commit()
    db.refresh(faction)

    create_default_faction_roles(db, faction.faction_id, user_id)

    # The documents folder is created on the first document write
    # (api/documentation.py), so nothing to do on disk here.
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
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while updating faction %s", faction.faction_id)
        raise HTTPException(status_code=500, detail="Database error occurred")


def delete_faction(db: Session, faction: Faction) -> None:
    try:
        db.delete(faction)
        db.commit()
    except IntegrityError:
        # Members, or transactions/history that reference the faction, are
        # still attached to it.
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This faction is still referenced (members or trade history) and can't be deleted",
        )
