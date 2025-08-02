from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ..enums import OfferAction


# ----- BASE -----
class OfferHistoryBase(BaseModel):
    offer_id: int
    actor_user_id: Optional[int] = None
    actor_faction_id: Optional[int] = None
    action: OfferAction
    notes: Optional[str] = None


# ----- CREATE -----
class OfferHistoryCreate(OfferHistoryBase):
    pass


# ----- OUTPUT -----
class OfferHistoryOut(OfferHistoryBase):
    history_id: int
    timestamp: datetime

    class Config:
        from_attributes = True
