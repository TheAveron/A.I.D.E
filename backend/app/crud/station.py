"""Stations and their platforms.

Anybody may register a station; changing one is for its creator and for the
train admins. Every function that writes commits, and turns a name clash into
a 409 rather than a 500.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import GlobalRoleName, LineStop, Platform, Station, User
from ..misc import StationDimension
from ..schemas import (
    PlatformCreate,
    PlatformUpdate,
    StationCreate,
    StationUpdate,
)

# A cap per user so one account cannot flood the index (train admins exempt).
MAX_STATIONS_PER_USER = 100
MAX_PLATFORMS_PER_STATION = 30


def is_train_admin(user: User) -> bool:
    return user.has_global_role(GlobalRoleName.TRAIN_ADMIN.value)


def can_manage_station(user: User, station: Station) -> bool:
    return is_train_admin(user) or station.created_by_user_id == user.user_id


def check_can_manage_station(user: User, station: Station) -> None:
    if not can_manage_station(user, station):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the station's creator or a train admin can change it",
        )


def get_station(db: Session, station_id: int) -> Station:
    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Station not found"
        )
    return station


def list_stations(
    db: Session,
    search: Optional[str] = None,
    dimension: Optional[StationDimension] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Station]:
    query = db.query(Station)
    if search and search.strip():
        # "%" and "_" typed by the user are plain characters here
        escaped = (
            search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        query = query.filter(Station.name.ilike(f"%{escaped}%", escape="\\"))
    if dimension is not None:
        query = query.filter(Station.dimension == dimension.value)
    return (
        query.order_by(func.lower(Station.name), Station.station_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def _name_taken(db: Session) -> HTTPException:
    db.rollback()
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="A station with this name already exists",
    )


def create_station(db: Session, user: User, data: StationCreate) -> Station:
    if not is_train_admin(user):
        mine = db.query(Station).filter(Station.created_by_user_id == user.user_id)
        if mine.count() >= MAX_STATIONS_PER_USER:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You already registered {MAX_STATIONS_PER_USER} stations",
            )
    station = Station(
        name=data.name,
        description=data.description,
        x=data.x,
        y=data.y,
        z=data.z,
        dimension=data.dimension.value,
        created_by_user_id=user.user_id,
        platforms=[
            Platform(name=p.name, description=p.description) for p in data.platforms
        ],
    )
    db.add(station)
    try:
        db.commit()
    except IntegrityError:
        raise _name_taken(db)
    db.refresh(station)
    return station


def update_station(db: Session, station: Station, data: StationUpdate) -> Station:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(station, field, value.value if field == "dimension" else value)
    try:
        db.commit()
    except IntegrityError:
        raise _name_taken(db)
    db.refresh(station)
    return station


def delete_station(db: Session, station: Station) -> None:
    if db.query(LineStop).filter(LineStop.station_id == station.station_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This station still serves a line: remove it from the line first",
        )
    db.delete(station)
    db.commit()


# ---- platforms ----


def _platform_clash(db: Session, station_id: int, name: str, except_id=None) -> None:
    query = db.query(Platform).filter(
        Platform.station_id == station_id, func.lower(Platform.name) == name.lower()
    )
    if except_id is not None:
        query = query.filter(Platform.platform_id != except_id)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This station already has a platform with this name",
        )


def get_platform(db: Session, station: Station, platform_id: int) -> Platform:
    platform = (
        db.query(Platform)
        .filter(
            Platform.platform_id == platform_id,
            Platform.station_id == station.station_id,
        )
        .first()
    )
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Platform not found"
        )
    return platform


def add_platform(db: Session, station: Station, data: PlatformCreate) -> Platform:
    if len(station.platforms) >= MAX_PLATFORMS_PER_STATION:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A station has at most {MAX_PLATFORMS_PER_STATION} platforms",
        )
    _platform_clash(db, station.station_id, data.name)
    platform = Platform(
        station_id=station.station_id, name=data.name, description=data.description
    )
    db.add(platform)
    db.commit()
    db.refresh(platform)
    return platform


def update_platform(db: Session, platform: Platform, data: PlatformUpdate) -> Platform:
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes:
        _platform_clash(db, platform.station_id, changes["name"], platform.platform_id)
    for field, value in changes.items():
        setattr(platform, field, value)
    db.commit()
    db.refresh(platform)
    return platform


def delete_platform(db: Session, platform: Platform) -> None:
    db.delete(platform)
    db.commit()
