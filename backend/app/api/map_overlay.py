"""What is drawn over the maps: faction territories and points of interest.

Anyone can read; changes follow crud/map_overlay.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import audit
from ..crud import map_overlay as crud
from ..database import User, get_db
from ..schemas import (MarkerCreate, MarkerOut, MarkerUpdate, TerritoryCreate,
                       TerritoryOut, TerritoryUpdate)
from ..schemas.map_overlay import MAP_NAME_RE

router = APIRouter(prefix="/map", tags=["Map"])


def _map_name(map_name: str = Path(..., max_length=50)) -> str:
    if not MAP_NAME_RE.match(map_name):
        raise HTTPException(status_code=404, detail="Map not found")
    return map_name


@router.get("/{map_name}/territories", response_model=list[TerritoryOut])
def list_territories(map_name: str = Depends(_map_name), db: Session = Depends(get_db)):
    return crud.list_territories(db, map_name)


@router.post(
    "/territories", response_model=TerritoryOut, status_code=status.HTTP_201_CREATED
)
def create_territory(
    body: TerritoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    territory, override = crud.create_territory(db, current_user, body)
    if override:
        audit.record(
            db,
            current_user,
            audit.AuditAction.TERRITORY_CHANGED,
            "territory",
            territory.territory_id,
            territory.name,
            f"Création pour la faction {territory.faction_name}",
        )
    db.commit()
    db.refresh(territory)
    return territory


@router.put("/territories/{territory_id}", response_model=TerritoryOut)
def update_territory(
    territory_id: int,
    body: TerritoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    territory = crud.get_territory(db, territory_id)
    crud.check_can_manage_territory(current_user, territory)
    override = crud.is_territory_override(current_user, territory)
    old_name = territory.name
    crud.update_territory(db, territory, body)
    if override:
        audit.record(
            db,
            current_user,
            audit.AuditAction.TERRITORY_CHANGED,
            "territory",
            territory.territory_id,
            old_name,
            f"Faction {territory.faction_name}",
        )
    db.commit()
    db.refresh(territory)
    return territory


@router.delete("/territories/{territory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_territory(
    territory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    territory = crud.get_territory(db, territory_id)
    crud.check_can_manage_territory(current_user, territory)
    if crud.is_territory_override(current_user, territory):
        audit.record(
            db,
            current_user,
            audit.AuditAction.TERRITORY_DELETED,
            "territory",
            territory.territory_id,
            territory.name,
            f"Faction {territory.faction_name}",
        )
    db.delete(territory)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{map_name}/markers", response_model=list[MarkerOut])
def list_markers(map_name: str = Depends(_map_name), db: Session = Depends(get_db)):
    return crud.list_markers(db, map_name)


@router.post("/markers", response_model=MarkerOut, status_code=status.HTTP_201_CREATED)
def create_marker(
    body: MarkerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    marker, override = crud.create_marker(db, current_user, body)
    if override:
        audit.record(
            db,
            current_user,
            audit.AuditAction.MARKER_CHANGED,
            "marker",
            marker.marker_id,
            marker.label,
            f"Création pour {marker.owner_name}",
        )
    db.commit()
    db.refresh(marker)
    return marker


@router.put("/markers/{marker_id}", response_model=MarkerOut)
def update_marker(
    marker_id: int,
    body: MarkerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    marker = crud.get_marker(db, marker_id)
    crud.check_can_manage_marker(current_user, marker)
    override = crud.is_marker_override(current_user, marker) or (
        current_user.is_admin and crud.is_spawn(body.kind)
    )
    old_label = marker.label
    crud.update_marker(db, current_user, marker, body)
    if override:
        audit.record(
            db,
            current_user,
            audit.AuditAction.MARKER_CHANGED,
            "marker",
            marker.marker_id,
            old_label,
            f"Appartient à {marker.owner_name}",
        )
    db.commit()
    db.refresh(marker)
    return marker


@router.delete("/markers/{marker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_marker(
    marker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    marker = crud.get_marker(db, marker_id)
    crud.check_can_manage_marker(current_user, marker)
    crud.check_spawn_rules(db, current_user, marker.map_name, current=marker)
    if crud.is_marker_override(current_user, marker):
        audit.record(
            db,
            current_user,
            audit.AuditAction.MARKER_DELETED,
            "marker",
            marker.marker_id,
            marker.label,
            f"Appartenait à {marker.owner_name}",
        )
    db.delete(marker)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
