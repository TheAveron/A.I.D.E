import logging
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import Faction, User
from ..database.clock import utcnow
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
    for faction_id, existing in db.query(Faction.faction_id, Faction.name).filter(
        Faction.deleted_at.is_(None)
    ):
        if faction_id != exclude_faction_id and normalize(existing) == key:
            return True
    return False


def list_factions(db: Session, skip: int = 0, limit: int = 100) -> list[Faction]:
    return (
        db.query(Faction)
        .filter(Faction.deleted_at.is_(None))
        .order_by(Faction.faction_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_members(db: Session) -> dict[int, int]:
    """Number of users of every faction (0 for the ones nobody belongs to)."""
    rows = (
        db.query(Faction.faction_id, func.count(User.user_id))
        .outerjoin(User, User.faction_id == Faction.faction_id)
        .filter(Faction.deleted_at.is_(None))
        .group_by(Faction.faction_id)
        .all()
    )
    return {faction_id: count for faction_id, count in rows}


def create_faction(db: Session, faction_data: FactionCreate, user_id: int) -> Faction:
    """Create a faction, its default roles and make `user_id` its leader.

    All of it is one transaction: either the faction exists with its roles and
    its leader, or nothing was created.
    """
    faction = Faction(
        name=faction_data.name,
        description=faction_data.description,
    )
    db.add(faction)
    try:
        db.flush()  # assigns faction_id and checks the unique name
        create_default_faction_roles(db, faction.faction_id, user_id, commit=False)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Faction name already exists")
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while creating faction %s", faction_data.name)
        raise HTTPException(status_code=500, detail="Database error occurred")

    db.refresh(faction)

    # The documents folder is created on the first document write
    # (api/documentation.py), so nothing to do on disk here.
    return faction


def update_faction_validation(
    db: Session, faction: Faction, faction_update: FactionUpdate
):
    try:
        for key, value in faction_update.model_dump(exclude_unset=True).items():
            setattr(faction, key, value)
        db.commit()
        db.refresh(faction)
        return faction
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error while updating faction %s", faction.faction_id)
        raise HTTPException(status_code=500, detail="Database error occurred")


NO_FACTION_NAME = "Sans Faction"
MEMBER_ROLE_NAME = "Membre"


def archive_faction(db: Session, faction: Faction, actor: User) -> None:
    """Delete a faction the way history allows: archive it.

    In the caller's transaction (nothing is committed here):
    - its open offers are cancelled (with a history entry each) and pending
      join requests withdrawn;
    - every member goes back to "Sans Faction";
    - its currency is deleted unless offers or transactions use it;
    - the faction is renamed "<name> [supprimée #id]" - which frees the
      unique name - and stamped `deleted_at`. Its row stays because closed
      offers and transactions refer to it.
    """
    from ..database import Offer
    from ..misc import OfferAction, OfferStatus
    from .currencies import is_currency_referenced
    from .offer_history import create_offer_history

    no_faction = get_faction_by_name(db, NO_FACTION_NAME)
    member_role = None
    if no_faction:
        member_role = next(
            (r for r in no_faction.roles if r.name == MEMBER_ROLE_NAME), None
        )
    if not no_faction or not member_role:
        raise HTTPException(
            status_code=503, detail=f'The "{NO_FACTION_NAME}" faction is not set up'
        )

    now = utcnow()

    for offer in db.query(Offer).filter(
        Offer.faction_id == faction.faction_id, Offer.status == OfferStatus.OPEN
    ):
        offer.status = OfferStatus.CANCELLED
        offer.updated_at = now
        create_offer_history(
            db,
            offer.offer_id,
            OfferAction.CANCELLED,
            actor_faction_id=faction.faction_id,
            notes=f"Offer cancelled: the faction was deleted by {actor.username}",
            commit=False,
        )

    for request in faction.join_requests:
        if request.status == "PENDING":
            request.status = "CANCELLED"
            request.decided_at = now

    for member in db.query(User).filter(User.faction_id == faction.faction_id):
        member.faction_id = no_faction.faction_id
        member.role_id = member_role.role_id

    currency = faction.currency
    if currency and not is_currency_referenced(db, currency.name):
        db.delete(currency)

    suffix = f" [supprimée #{faction.faction_id}]"
    faction.name = faction.name[: 100 - len(suffix)] + suffix
    faction.deleted_at = now
