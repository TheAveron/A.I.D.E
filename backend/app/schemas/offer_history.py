from typing import Optional

from pydantic import BaseModel

from .base import UTCDatetime

from ..misc import OfferAction


class OfferHistoryBase(BaseModel):
    offer_id: int
    actor_user_id: Optional[int] = None
    actor_faction_id: Optional[int] = None
    action: OfferAction
    notes: Optional[str] = None


class OfferHistoryCreate(OfferHistoryBase):
    pass


class OfferHistoryOut(OfferHistoryBase):
    history_id: int
    timestamp: UTCDatetime

    class Config:
        from_attributes = True
