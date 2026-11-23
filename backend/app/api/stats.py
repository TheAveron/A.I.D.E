"""Public figures about the server, for the home page."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..crud.faction import NO_FACTION_NAME
from ..database import Faction, GlobalRole, GlobalRoleName, MapMarker, User, get_db
from ..misc import MarkerKind

router = APIRouter(prefix="/stats", tags=["Stats"])


class PublicStats(BaseModel):
    # Accounts, the admins' left out (they run the server, they don't play it)
    members: int
    # Towns and projects placed on the maps
    projects: int
    # Approved factions that still exist
    factions: int


@router.get("", response_model=PublicStats)
def public_stats(db: Session = Depends(get_db)):
    admins = (
        db.query(func.count(GlobalRole.user_id))
        .filter(GlobalRole.role == GlobalRoleName.ADMIN.value)
        .scalar()
    )
    users = db.query(func.count(User.user_id)).scalar()
    projects = (
        db.query(func.count(MapMarker.marker_id))
        .filter(MapMarker.kind == MarkerKind.CITY.value)
        .scalar()
    )
    factions = (
        db.query(func.count(Faction.faction_id))
        .filter(
            Faction.is_approved.is_(True),
            Faction.deleted_at.is_(None),
            Faction.name != NO_FACTION_NAME,
        )
        .scalar()
    )
    return PublicStats(
        members=max(users - admins, 0), projects=projects, factions=factions
    )
