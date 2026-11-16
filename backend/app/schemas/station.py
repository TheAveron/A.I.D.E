from typing import Annotated, Optional

from pydantic import (AfterValidator, BaseModel, ConfigDict, Field,
                      field_validator)

from ..misc import StationDimension
from .base import MAX_DESCRIPTION_LENGTH, PartialUpdate, UTCDatetime

# Minecraft's world border; y is the build height, with room for data packs.
MAX_XZ = 30_000_000
MAX_Y = 2048
MAX_PLATFORMS = 30


def _stripped_not_blank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Cannot be blank")
    return value


Name = Annotated[str, AfterValidator(_stripped_not_blank)]


class PlatformCreate(BaseModel):
    name: Name = Field(..., min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=300)


class PlatformUpdate(PartialUpdate):
    non_nullable = ("name",)

    name: Optional[Name] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=300)


class PlatformOut(BaseModel):
    platform_id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StationCreate(BaseModel):
    name: Name = Field(..., min_length=1, max_length=60)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    x: int = Field(..., ge=-MAX_XZ, le=MAX_XZ)
    y: Optional[int] = Field(None, ge=-MAX_Y, le=MAX_Y)
    z: int = Field(..., ge=-MAX_XZ, le=MAX_XZ)
    dimension: StationDimension = StationDimension.OVERWORLD
    platforms: list[PlatformCreate] = Field(
        default_factory=list, max_length=MAX_PLATFORMS
    )

    @field_validator("platforms")
    @classmethod
    def _platform_names_differ(cls, platforms: list[PlatformCreate]):
        names = [p.name.lower() for p in platforms]
        if len(names) != len(set(names)):
            raise ValueError("Two platforms cannot have the same name")
        return platforms


class StationUpdate(PartialUpdate):
    non_nullable = ("name", "x", "z", "dimension")

    name: Optional[Name] = Field(None, min_length=1, max_length=60)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    x: Optional[int] = Field(None, ge=-MAX_XZ, le=MAX_XZ)
    y: Optional[int] = Field(None, ge=-MAX_Y, le=MAX_Y)
    z: Optional[int] = Field(None, ge=-MAX_XZ, le=MAX_XZ)
    dimension: Optional[StationDimension] = None


class StationOut(BaseModel):
    station_id: int
    name: str
    description: Optional[str] = None
    x: int
    y: Optional[int] = None
    z: int
    dimension: StationDimension
    created_by_user_id: Optional[int] = None
    created_at: UTCDatetime
    updated_at: UTCDatetime
    platforms: list[PlatformOut] = []

    model_config = ConfigDict(from_attributes=True)
