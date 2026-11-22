"""Territories and points of interest on the maps.

- a faction's territories and markers are changed by members holding
  `manage_territory` in that faction, and by admins, who may change anything;
- a player's own territories and markers are theirs to change (and admins'):
  anybody logged in may draw land for themselves;
- anybody can read all of it;
- only the current server's maps change: the archived ones are frozen.

The audit trail only records an admin acting on what is not theirs.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import Faction, MapMarker, MapTerritory, User
from ..database.clock import utcnow
from ..misc import (CURRENT_MAPS, STRUCTURE_KINDS, FactionPermission,
                    MarkerKind, check_faction_permission)
from ..schemas import (MarkerCreate, MarkerUpdate, TerritoryCreate,
                       TerritoryUpdate)

MAX_TERRITORIES_PER_FACTION = 20
MAX_TERRITORIES_PER_USER = 5
MAX_MARKERS_PER_FACTION = 200
MAX_MARKERS_PER_USER = 50


def _error(code: int, detail: str) -> HTTPException:
    return HTTPException(status_code=code, detail=detail)


def check_map_is_current(map_name: str) -> None:
    """Refuse any change on a map of the archives (a former server's)."""
    if map_name not in CURRENT_MAPS:
        raise _error(
            status.HTTP_403_FORBIDDEN, "The maps of the archives can't be changed"
        )


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
        .outerjoin(Faction, Faction.faction_id == MapTerritory.faction_id)
        .filter(
            MapTerritory.map_name == map_name,
            (MapTerritory.faction_id.is_(None)) | (Faction.deleted_at.is_(None)),
        )
        .order_by(MapTerritory.territory_id)
        .all()
    )


def get_territory(db: Session, territory_id: int) -> MapTerritory:
    territory = db.get(MapTerritory, territory_id)
    if not territory:
        raise _error(status.HTTP_404_NOT_FOUND, "Territory not found")
    return territory


def _owns_territory(user: User, territory: MapTerritory) -> bool:
    """The rights that come from owning it, without the admin's."""
    if territory.user_id is not None:
        return territory.user_id == user.user_id
    return holds_manage_territory(user, territory.faction_id)


def can_manage_territory(user: User, territory: MapTerritory) -> bool:
    return user.is_admin or _owns_territory(user, territory)


def check_can_manage_territory(user: User, territory: MapTerritory) -> None:
    check_map_is_current(territory.map_name)
    if not can_manage_territory(user, territory):
        raise _error(
            status.HTTP_403_FORBIDDEN,
            "A faction's territory needs manage_territory in it; "
            "a player's is theirs alone",
        )


def is_territory_override(user: User, territory: MapTerritory) -> bool:
    return user.is_admin and not _owns_territory(user, territory)


def _name_taken() -> HTTPException:
    return _error(
        status.HTTP_409_CONFLICT, "This owner already has a territory of that name"
    )


def create_territory(
    db: Session, user: User, data: TerritoryCreate
) -> tuple[MapTerritory, bool]:
    """Returns the territory and whether an admin made it for somebody else.

    A faction's needs manage_territory in it; without that, a member (like
    anybody logged in) draws only for themselves.
    """
    check_map_is_current(data.map_name)
    fields = data.model_dump(exclude={"faction_id", "user_id"})
    if data.faction_id is not None:
        _live_faction(db, data.faction_id)
        holds = holds_manage_territory(user, data.faction_id)
        if not user.is_admin and not holds:
            raise _error(
                status.HTTP_403_FORBIDDEN,
                "Drawing a faction's territory needs manage_territory in it",
            )
        override = user.is_admin and not holds
        owner, limit = {"faction_id": data.faction_id}, MAX_TERRITORIES_PER_FACTION
        too_many = f"A faction has at most {limit} territories per map"
    else:
        owner_id = data.user_id if data.user_id is not None else user.user_id
        override = owner_id != user.user_id
        if override:
            if not user.is_admin:
                raise _error(
                    status.HTTP_403_FORBIDDEN,
                    "You can only draw your own territories",
                )
            if not db.get(User, owner_id):
                raise _error(status.HTTP_404_NOT_FOUND, "User not found")
        owner, limit = {"user_id": owner_id}, MAX_TERRITORIES_PER_USER
        too_many = f"A player has at most {limit} territories per map"
    count = db.query(MapTerritory).filter_by(map_name=data.map_name, **owner).count()
    if count >= limit:
        raise _error(status.HTTP_409_CONFLICT, too_many)
    territory = MapTerritory(**fields, **owner, created_by_user_id=user.user_id)
    db.add(territory)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise _name_taken()
    return territory, override


def update_territory(
    db: Session, territory: MapTerritory, data: TerritoryUpdate
) -> MapTerritory:
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(territory, name, value)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise _name_taken()
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
    check_map_is_current(marker.map_name)
    if not can_manage_marker(user, marker):
        raise _error(status.HTTP_403_FORBIDDEN, "You can't change this marker")


def is_spawn(kind) -> bool:
    return getattr(kind, "value", kind) == MarkerKind.SPAWN.value


def check_spawn_rules(
    db: Session,
    user: User,
    map_name: str,
    *,
    current: Optional[MapMarker] = None,
    new_kind=None,
) -> None:
    """The spawn is one per map, and only an admin places, moves or removes it.

    `current` is the marker being changed or deleted, `new_kind` the kind that
    a creation or an update asks for.
    """
    touches_spawn = is_spawn(new_kind) or (
        current is not None and is_spawn(current.kind)
    )
    if not touches_spawn:
        return
    if not user.is_admin:
        raise _error(
            status.HTTP_403_FORBIDDEN, "Only an admin can place or move the spawn"
        )
    if is_spawn(new_kind) and not (current is not None and is_spawn(current.kind)):
        taken = (
            db.query(MapMarker)
            .filter(MapMarker.map_name == map_name, MapMarker.kind == "spawn")
            .first()
        )
        if taken:
            raise _error(
                status.HTTP_409_CONFLICT,
                "This map already has a spawn: move it instead",
            )


def check_not_a_station(kind) -> None:
    """A station is a real station (crud/station.py), never a bare marker:
    otherwise it would show on the map but not in the index of stations."""
    if getattr(kind, "value", kind) == MarkerKind.STATION.value:
        raise _error(
            status.HTTP_400_BAD_REQUEST,
            "A station is registered as a station, not as a marker",
        )


def is_marker_override(user: User, marker: MapMarker) -> bool:
    if not user.is_admin:
        return False
    if is_spawn(marker.kind):
        return True  # the spawn is common property: every change is audited
    if marker.user_id is not None:
        return marker.user_id != user.user_id
    return not holds_manage_territory(user, marker.faction_id)


def create_marker(
    db: Session, user: User, data: MarkerCreate
) -> tuple[MapMarker, bool]:
    """Returns the marker and whether an admin made it for somebody else."""
    check_map_is_current(data.map_name)
    fields = data.model_dump(exclude={"faction_id", "user_id"})
    override = False
    check_not_a_station(data.kind)
    check_spawn_rules(db, user, data.map_name, new_kind=data.kind)
    if is_spawn(data.kind):
        # Nobody owns the spawn: it is stored under the admin who sets it
        if data.faction_id is not None or data.user_id not in (None, user.user_id):
            raise _error(status.HTTP_400_BAD_REQUEST, "The spawn has no owner")
        override = True
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
    if marker.kind != MarkerKind.GENERIC.value:
        marker.color = None  # the icon says what it is
    db.add(marker)
    db.flush()
    return marker, override


def update_marker(
    db: Session, user: User, marker: MapMarker, data: MarkerUpdate
) -> MapMarker:
    check_spawn_rules(db, user, marker.map_name, current=marker, new_kind=data.kind)
    check_not_a_station(data.kind)
    for name, value in data.model_dump(exclude_unset=True).items():
        setattr(marker, name, value.value if hasattr(value, "value") else value)
    if marker.kind not in STRUCTURE_KINDS:
        _forget_explored(marker)  # only a structure has loot to take
    if marker.kind != MarkerKind.GENERIC.value:
        marker.color = None  # only a generic point is a coloured dot
    db.flush()
    return marker


# ---- explored structures ----


def _forget_explored(marker: MapMarker) -> None:
    marker.explored = False
    marker.explored_by_user_id = None
    marker.explored_at = None


def set_explored(
    db: Session, user: User, marker: MapMarker, explored: bool
) -> MapMarker:
    """Anybody logged in may tell that a structure was looted (whoever placed
    it is rarely the one who loots it); the map shows who said so, and when."""
    check_map_is_current(marker.map_name)
    if marker.kind not in STRUCTURE_KINDS:
        raise _error(
            status.HTTP_400_BAD_REQUEST, "Only a structure can be marked as explored"
        )
    if not explored:
        _forget_explored(marker)
    elif not marker.explored:
        # Marking it again keeps the first explorer
        marker.explored = True
        marker.explored_by_user_id = user.user_id
        marker.explored_at = utcnow()
    db.flush()
    return marker
