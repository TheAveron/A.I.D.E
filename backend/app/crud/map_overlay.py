"""Territories and points of interest on the maps.

- a faction's territories and markers are changed by members holding
  `manage_territory` in that faction, and by admins, who may change anything;
- a player's own markers are theirs to change (and admins');
- anybody can read all of it.

The audit trail only records an admin acting on what is not theirs.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import Faction, MapMarker, MapTerritory, User
from ..misc import FactionPermission, check_faction_permission
from ..schemas import (MarkerCreate, MarkerUpdate, TerritoryCreate,
                       TerritoryUpdate)

MAX_TERRITORIES_PER_FACTION = 20
MAX_MARKERS_PER_FACTION = 200
MAX_MARKERS_PER_USER = 50


def _error(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def holds_manage_territory(user: User, faction_id: Optional[int]) -> bool:
    if faction_id is None:
        return False
    try:
        check_faction_permission(
            user, FactionPermission.MANAGE_TERRITORY, target_faction_id=faction_id
        )
    except HTTPException:
        return False
    return True


def _live_faction(db: Session, faction_id: int) -> Faction:
    faction = (
        db.query(Faction)
        .filter(Faction.faction_id == faction_id, Faction.deleted_at.is_(None))
        .first()
    )
    if not faction:
        raise _error(status.HTTP_404_NOT_FOUND, "Faction not found")
    return faction


# ---- territories ----


def list_territories(db: Session, map_name: str) -> list[MapTerritory]:
    return (
        db.query(MapTerritory)
        .join(Faction, Faction.faction_id == MapTerritory.faction_id)
        .filter(MapTerritory.map_name == map_name, Faction.deleted_at.is_(None))
        .order_by(MapTerritory.territory_id)
        .all()
    )


def get_territory(db: Session, territory_id: int) -> MapTerritory:
    territory = db.get(MapTerritory, territory_id)
    if not territory:
        raise _error(status.HTTP_404_NOT_FOUND, "Territory not found")
    return territory


def can_manage_territory(user: User, territory: MapTerritory) -> bool:
    return user.is_admin or holds_manage_territory(user, territory.faction_id)


def check_can_manage_territory(user: User, territory: MapTerritory) -> None:
    if not can_manage_territory(user, territory):
        raise _error(
            status.HTTP_403_FORBIDDEN,
            "Changing a faction's territory needs manage_territory in it",
        )


def is_territory_override(user: User, territory: MapTerritory) -> bool:
    return user.is_admin and not holds_manage_territory(user, territory.faction_id)


def create_territory(
    db: Session, user: User, data: TerritoryCreate
) -> tuple[MapTerritory, bool]:
    """Returns the territory and whether an admin made it for another faction."""
    _live_faction(db, data.faction_id)
    holds = holds_manage_territory(user, data.faction_id)
    if not user.is_admin and not holds:
        raise _error(
            status.HTTP_403_FORBIDDEN,
            "Drawing a faction's territory needs manage_territory in it",
        )
    count = (
        db.query(MapTerritory)
        .filter_by(map_name=data.map_name, faction_id=data.faction_id)
        .count()
    )
    if count >= MAX_TERRITORIES_PER_FACTION:
        raise _error(
            status.HTTP_409_CONFLICT,
            f"A faction has at most {MAX_TERRITORIES_PER_FACTION} territories per map",
        )
    territory = MapTerritory(**data.model_dump(), created_by_user_id=user.user_id)
    db.add(territory)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise _error(
            status.HTTP_409_CONFLICT,
            "This faction already has a territory of that name",
        )
    return territory, user.is_admin and not holds


def update_territory(
    db: Session, territory: MapTerritory, data: TerritoryUpdate
) -> MapTerritory:
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(territory, name, value)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise _error(
            status.HTTP_409_CONFLICT,
            "This faction already has a territory of that name",
        )
    return territory


# ---- markers ----


def list_markers(db: Session, map_name: str) -> list[MapMarker]:
    return (
        db.query(MapMarker)
        .outerjoin(Faction, Faction.faction_id == MapMarker.faction_id)
        .filter(
            MapMarker.map_name == map_name,
            (MapMarker.faction_id.is_(None)) | (Faction.deleted_at.is_(None)),
        )
        .order_by(MapMarker.marker_id)
        .all()
    )


def get_marker(db: Session, marker_id: int) -> MapMarker:
    marker = db.get(MapMarker, marker_id)
    if not marker:
        raise _error(status.HTTP_404_NOT_FOUND, "Marker not found")
    return marker


def can_manage_marker(user: User, marker: MapMarker) -> bool:
    if user.is_admin:
        return True
    if marker.user_id is not None:
        return marker.user_id == user.user_id
    return holds_manage_territory(user, marker.faction_id)


def check_can_manage_marker(user: User, marker: MapMarker) -> None:
    if not can_manage_marker(user, marker):
        raise _error(status.HTTP_403_FORBIDDEN, "You can't change this marker")


def is_marker_override(user: User, marker: MapMarker) -> bool:
    if not user.is_admin:
        return False
    if marker.user_id is not None:
        return marker.user_id != user.user_id
    return not holds_manage_territory(user, marker.faction_id)


def create_marker(
    db: Session, user: User, data: MarkerCreate
) -> tuple[MapMarker, bool]:
    """Returns the marker and whether an admin made it for somebody else."""
    fields = data.model_dump(exclude={"faction_id", "user_id"})
    override = False
    if data.faction_id is not None:
        _live_faction(db, data.faction_id)
        holds = holds_manage_territory(user, data.faction_id)
        if not user.is_admin and not holds:
            raise _error(
                status.HTTP_403_FORBIDDEN,
                "A faction's marker needs manage_territory in it",
            )
        override = user.is_admin and not holds
        count = (
            db.query(MapMarker)
            .filter_by(map_name=data.map_name, faction_id=data.faction_id)
            .count()
        )
        if count >= MAX_MARKERS_PER_FACTION:
            raise _error(
                status.HTTP_409_CONFLICT,
                f"A faction has at most {MAX_MARKERS_PER_FACTION} markers per map",
            )
        owner = {"faction_id": data.faction_id}
    else:
        owner_id = data.user_id if data.user_id is not None else user.user_id
        if owner_id != user.user_id:
            if not user.is_admin:
                raise _error(
                    status.HTTP_403_FORBIDDEN, "You can only place your own markers"
                )
            if not db.get(User, owner_id):
                raise _error(status.HTTP_404_NOT_FOUND, "User not found")
            override = True
        count = (
            db.query(MapMarker)
            .filter_by(map_name=data.map_name, user_id=owner_id)
            .count()
        )
        if count >= MAX_MARKERS_PER_USER:
            raise _error(
                status.HTTP_409_CONFLICT,
                f"A player has at most {MAX_MARKERS_PER_USER} markers per map",
            )
        owner = {"user_id": owner_id}
    marker = MapMarker(**fields, **owner)
    db.add(marker)
    db.flush()
    return marker, override


def update_marker(db: Session, marker: MapMarker, data: MarkerUpdate) -> MapMarker:
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(marker, name, value.value if hasattr(value, "value") else value)
    db.flush()
    return marker
