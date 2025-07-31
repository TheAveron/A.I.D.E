from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class OfferType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OfferStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class OfferBase(BaseModel):
    offer_type: OfferType
    item_description: Dict[str, Union[str, int, float]]  # flexible structure
    currency: str
    price_per_unit: float
    quantity: int
    allowed_parties: Optional[List[int]] = None  # list of allowed user/faction IDs


class OfferCreate(OfferBase):
    user_id: Optional[int] = None
    faction_id: Optional[int] = None


class OfferUpdate(BaseModel):
    status: Optional[OfferStatus] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    allowed_parties: Optional[List[int]] = None


class OfferOut(OfferBase):
    id: int
    user_id: Optional[int]
    faction_id: Optional[int]
    status: OfferStatus
    created_at: datetime

    class Config:
        from_attributes = True


class OfferHistoryOut(BaseModel):
    id: int
    offer_id: int
    action: str
    actor_user_id: Optional[int] = None
    actor_faction_id: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True
