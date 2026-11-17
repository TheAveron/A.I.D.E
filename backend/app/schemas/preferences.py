from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

from .base import PartialUpdate

Theme = Literal["system", "dark", "light"]


class PreferencesOut(BaseModel):
    theme: Theme
    notify_market: bool
    notify_faction: bool

    model_config = ConfigDict(from_attributes=True)


class PreferencesUpdate(PartialUpdate):
    theme: Optional[Theme] = None
    notify_market: Optional[bool] = None
    notify_faction: Optional[bool] = None

    non_nullable = ("theme", "notify_market", "notify_faction")
