from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class OfferType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OfferStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


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
    price_per_unit: Optional[float] = None
    quantity: Optional[int] = None
    allowed_parties: Optional[List[int]] = None


class OfferOut(OfferBase):
    id: int
    user_id: Optional[int]
    faction_id: Optional[int]
    status: OfferStatus
    created_at: datetime

    class Config:
        orm_mode = True
