"""The index of stations: readable by everybody, registered by any account."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import station as crud
from ..database import User, get_db
from ..misc import StationDimension
from ..schemas import (
    PlatformCreate,
    PlatformOut,
    PlatformUpdate,
    StationCreate,
    StationOut,
    StationUpdate,
)

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=list[StationOut])
def list_stations(
    q: Optional[str] = Query(None, max_length=60, description="Words in the name"),
    dimension: Optional[StationDimension] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    db: Session = Depends(get_db),
):
    return crud.list_stations(db, q, dimension, skip, limit)


@router.get("/{station_id}", response_model=StationOut)
def read_station(station_id: int, db: Session = Depends(get_db)):
    return crud.get_station(db, station_id)


@router.post("", response_model=StationOut, status_code=status.HTTP_201_CREATED)
def create_station(
    station_in: StationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_station(db, current_user, station_in)


@router.put("/{station_id}", response_model=StationOut)
def update_station(
    station_id: int,
    station_in: StationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    station = crud.get_station(db, station_id)
    crud.check_can_manage_station(current_user, station)
    return crud.update_station(db, station, station_in)


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_station(
    station_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    station = crud.get_station(db, station_id)
    crud.check_can_manage_station(current_user, station)
    crud.delete_station(db, station)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{station_id}/platforms",
    response_model=PlatformOut,
    status_code=status.HTTP_201_CREATED,
)
def add_platform(
    station_id: int,
    platform_in: PlatformCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    station = crud.get_station(db, station_id)
    crud.check_can_manage_station(current_user, station)
    return crud.add_platform(db, station, platform_in)


@router.put("/{station_id}/platforms/{platform_id}", response_model=PlatformOut)
def update_platform(
    station_id: int,
    platform_id: int,
    platform_in: PlatformUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    station = crud.get_station(db, station_id)
    crud.check_can_manage_station(current_user, station)
    platform = crud.get_platform(db, station, platform_id)
    return crud.update_platform(db, platform, platform_in)


@router.delete(
    "/{station_id}/platforms/{platform_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_platform(
    station_id: int,
    platform_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    station = crud.get_station(db, station_id)
    crud.check_can_manage_station(current_user, station)
    platform = crud.get_platform(db, station, platform_id)
    crud.delete_platform(db, platform)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
