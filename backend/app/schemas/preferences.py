from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import PartialUpdate

Theme = Literal["system", "dark", "light"]
MapLayer = Literal["territories", "stations", "markers", "players"]


class MapDisplay(BaseModel):
    """What the map shows, as the person left it. Only what is hidden is
    listed: a layer, a kind or a faction added later shows by default."""

    hidden_layers: list[MapLayer] = Field(default_factory=list, max_length=10)
    # MarkerKind values; an unknown one (a kind since removed) is harmless
    hidden_kinds: list[Annotated[str, Field(max_length=30)]] = Field(
        default_factory=list, max_length=50
    )
    # Faction ids; None stands for the players' own territories
    hidden_factions: list[Optional[int]] = Field(default_factory=list, max_length=500)


class PreferencesOut(BaseModel):
    theme: Theme
    notify_market: bool
    notify_faction: bool
    map_display: Optional[MapDisplay] = None

    model_config = ConfigDict(from_attributes=True)


class PreferencesUpdate(PartialUpdate):
    theme: Optional[Theme] = None
    notify_market: Optional[bool] = None
    notify_faction: Optional[bool] = None
    map_display: Optional[MapDisplay] = None

    non_nullable = ("theme", "notify_market", "notify_faction")
