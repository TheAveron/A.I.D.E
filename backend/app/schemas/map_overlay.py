import re
from typing import Annotated, Optional

from pydantic import (BaseModel, ConfigDict, Field, field_validator,
                      model_validator)

from ..misc import MarkerKind
from .base import MAX_DESCRIPTION_LENGTH, PartialUpdate, UTCDatetime

MAP_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,50}$")
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

# Minecraft's world limit; a coordinate outside it is a typo
COORD_LIMIT = 30_000_000
MIN_POINTS = 3
MAX_POINTS = 200

Coordinate = Annotated[int, Field(ge=-COORD_LIMIT, le=COORD_LIMIT)]


def _map_name(value: str) -> str:
    if not MAP_NAME_RE.match(value):
        raise ValueError("Invalid map name")
    return value


def _color(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    if not COLOR_RE.match(value):
        raise ValueError("The color must look like #1a2b3c")
    return value.lower()


def _polygon(points: list[list[int]]) -> list[list[int]]:
    if not MIN_POINTS <= len(points) <= MAX_POINTS:
        raise ValueError(f"A territory has {MIN_POINTS} to {MAX_POINTS} points")
    for point in points:
        if len(point) != 2 or any(abs(c) > COORD_LIMIT for c in point):
            raise ValueError("A point is [x, z] within the world limits")
    # Closing the ring by repeating the first point is not needed
    if points[0] == points[-1] and len(points) > MIN_POINTS:
        points = points[:-1]
    if len({tuple(p) for p in points}) < MIN_POINTS:
        raise ValueError("A territory needs 3 different points")
    # Shoelace: three points on one line enclose nothing
    twice_area = sum(
        points[i][0] * points[(i + 1) % len(points)][1]
        - points[(i + 1) % len(points)][0] * points[i][1]
        for i in range(len(points))
    )
    if twice_area == 0:
        raise ValueError("The points enclose no area")
    return points


class TerritoryCreate(BaseModel):
    map_name: str
    faction_id: int
    name: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    color: Optional[str] = None
    points: list[list[int]]

    _map = field_validator("map_name")(_map_name)
    _col = field_validator("color")(_color)
    _poly = field_validator("points")(_polygon)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("The name cannot be empty")
        return value


class TerritoryUpdate(PartialUpdate):
    non_nullable = ("name", "points")

    name: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    color: Optional[str] = None
    points: Optional[list[list[int]]] = None

    _col = field_validator("color")(_color)

    @field_validator("points")
    @classmethod
    def _poly(cls, value):
        return None if value is None else _polygon(value)

    @field_validator("name")
    @classmethod
    def _name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("The name cannot be empty")
        return value


class TerritoryOut(BaseModel):
    territory_id: int
    map_name: str
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    faction_id: int
    faction_name: Optional[str] = None
    points: list[list[int]]
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class MarkerCreate(BaseModel):
    map_name: str
    label: str = Field(..., min_length=1, max_length=60)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    kind: MarkerKind = MarkerKind.GENERIC
    x: Coordinate
    z: Coordinate
    # Only a generic point has a colour (the others have their icon)
    color: Optional[str] = None
    # Exactly one owner; neither means the caller themselves
    faction_id: Optional[int] = None
    user_id: Optional[int] = None

    _map = field_validator("map_name")(_map_name)
    _col = field_validator("color")(_color)

    @field_validator("label")
    @classmethod
    def _label(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("The label cannot be empty")
        return value

    @model_validator(mode="after")
    def _one_owner(self):
        if self.faction_id is not None and self.user_id is not None:
            raise ValueError("A marker belongs to a faction or to a player, not both")
        return self


class MarkerUpdate(PartialUpdate):
    non_nullable = ("label", "kind", "x", "z")

    label: Optional[str] = Field(None, min_length=1, max_length=60)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    kind: Optional[MarkerKind] = None
    x: Optional[Coordinate] = None
    z: Optional[Coordinate] = None
    color: Optional[str] = None

    _col = field_validator("color")(_color)

    @field_validator("label")
    @classmethod
    def _label(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("The label cannot be empty")
        return value


class MarkerOut(BaseModel):
    marker_id: int
    map_name: str
    label: str
    description: Optional[str] = None
    kind: str
    x: int
    z: int
    color: Optional[str] = None
    explored: bool = False
    explored_by_name: Optional[str] = None
    explored_at: Optional[UTCDatetime] = None
    faction_id: Optional[int] = None
    user_id: Optional[int] = None
    owner_name: Optional[str] = None
    created_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class MarkerExplored(BaseModel):
    explored: bool
