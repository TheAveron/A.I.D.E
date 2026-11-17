import re
from typing import Annotated, Optional

from pydantic import (AfterValidator, BaseModel, ConfigDict, Field,
                      PositiveInt, field_validator, model_validator)

from ..misc import StationDimension, TrainAction, TrainService
from .base import MAX_DESCRIPTION_LENGTH, PartialUpdate, UTCDatetime

MAX_STOPS = 100
MAINTENANCE_LINE = "Z"

_LINE_RE = re.compile(r"^[A-Y][1-9]?$")
_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def _line_code(value: str) -> str:
    value = value.strip().upper()
    if not (_LINE_RE.match(value) or value == MAINTENANCE_LINE):
        raise ValueError(
            "A line is a letter from A to Y, optionally followed by a digit "
            "from 1 to 9 (A, A2), or Z for maintenance"
        )
    return value


def _plain_text(value: str) -> str:
    """Stripped, without line breaks or control characters; '' becomes None."""
    value = value.strip()
    if _CONTROL_RE.search(value):
        raise ValueError("Control characters are not allowed")
    return value


LineCode = Annotated[str, AfterValidator(_line_code)]
PlainText = Annotated[str, AfterValidator(_plain_text)]


def _check_service(line: str, service: Optional[TrainService]) -> None:
    if line == MAINTENANCE_LINE and service is not None:
        raise ValueError("Maintenance trains (line Z) have no service")
    if line != MAINTENANCE_LINE and service is None:
        raise ValueError("A service (O, E, F or L) is required outside line Z")


# ---- lines ----


class LineCreate(BaseModel):
    code: LineCode
    name: Optional[PlainText] = Field(None, max_length=60)
    color: Optional[str] = Field(None, pattern=_COLOR_RE.pattern)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    owner_faction_id: Optional[PositiveInt] = None

    @field_validator("code")
    @classmethod
    def _not_maintenance(cls, value: str) -> str:
        if value == MAINTENANCE_LINE:
            raise ValueError("The line Z is reserved for maintenance")
        return value

    @field_validator("color")
    @classmethod
    def _lower_color(cls, value: Optional[str]) -> Optional[str]:
        return value.lower() if value else value


class LineUpdate(PartialUpdate):
    name: Optional[PlainText] = Field(None, max_length=60)
    color: Optional[str] = Field(None, pattern=_COLOR_RE.pattern)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    owner_faction_id: Optional[PositiveInt] = None

    @field_validator("color")
    @classmethod
    def _lower_color(cls, value: Optional[str]) -> Optional[str]:
        return value.lower() if value else value


class StopsUpdate(BaseModel):
    """The whole ordered list of stations; the first and last are the ends."""

    station_ids: list[PositiveInt] = Field(..., max_length=MAX_STOPS)

    @field_validator("station_ids")
    @classmethod
    def _no_repeat(cls, ids: list[int]) -> list[int]:
        if len(ids) != len(set(ids)):
            raise ValueError("A station can only appear once on a line")
        return ids


class StopStation(BaseModel):
    station_id: int
    name: str
    x: int
    y: Optional[int] = None
    z: int
    dimension: StationDimension

    model_config = ConfigDict(from_attributes=True)


class StopOut(BaseModel):
    position: int
    station: StopStation

    model_config = ConfigDict(from_attributes=True)


class LineOut(BaseModel):
    line_id: int
    code: str
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    owner_faction_id: Optional[int] = None
    stops: list[StopOut] = []

    model_config = ConfigDict(from_attributes=True)


# ---- trains ----


class TrainCreate(BaseModel):
    line: LineCode
    service: Optional[TrainService] = None
    common_name: Optional[PlainText] = Field(None, max_length=24)
    legacy_id: Optional[PlainText] = Field(None, max_length=50)
    # Neither: the train is the caller's. Never both.
    owner_user_id: Optional[PositiveInt] = None
    owner_faction_id: Optional[PositiveInt] = None

    @field_validator("service", mode="before")
    @classmethod
    def _upper_service(cls, value):
        return value.strip().upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _coherent(self):
        _check_service(self.line, self.service)
        if self.owner_user_id is not None and self.owner_faction_id is not None:
            raise ValueError("A train belongs to a player or to a faction, not both")
        return self


class TrainUpdate(PartialUpdate):
    non_nullable = ("line",)

    line: Optional[LineCode] = None
    service: Optional[TrainService] = None
    common_name: Optional[PlainText] = Field(None, max_length=24)
    legacy_id: Optional[PlainText] = Field(None, max_length=50)
    owner_user_id: Optional[PositiveInt] = None
    owner_faction_id: Optional[PositiveInt] = None

    @field_validator("service", mode="before")
    @classmethod
    def _upper_service(cls, value):
        return value.strip().upper() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _one_owner(self):
        if self.owner_user_id is not None and self.owner_faction_id is not None:
            raise ValueError("A train belongs to a player or to a faction, not both")
        return self


class TrainOut(BaseModel):
    train_id: int
    display_name: str
    line: str = Field(validation_alias="line_code")
    service: Optional[TrainService] = None
    number: int
    common_name: Optional[str] = None
    legacy_id: Optional[str] = None
    owner_user_id: Optional[int] = None
    owner_faction_id: Optional[int] = None
    owner_name: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_at: UTCDatetime
    updated_at: UTCDatetime
    retired_at: Optional[UTCDatetime] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TrainHistoryOut(BaseModel):
    history_id: int
    action: TrainAction
    old_name: Optional[str] = None
    new_name: Optional[str] = None
    actor_user_id: Optional[int] = None
    created_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)
