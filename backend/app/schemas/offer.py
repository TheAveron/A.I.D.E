from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..misc import OfferStatus, OfferType


# ----- BASE -----
class OfferBase(BaseModel):
    offer_type: OfferType
    item_description: str
    currency_name: str
    price_per_unit: float
    quantity: int
    init_quantity: int = 0
    allowed_parties: Optional[list[int]] = None


# ----- CREATE -----
class OfferCreate(OfferBase):
    user_id: Optional[int] = None
    faction_id: Optional[int] = None


# ----- UPDATE -----
class OfferUpdate(BaseModel):
    status: Optional[OfferStatus] = None
    price_per_unit: Optional[float] = None
    quantity: Optional[int] = None
    allowed_parties: Optional[list[int]] = None


# ----- OUTPUT -----
class OfferOut(OfferBase):
    offer_id: int
    user_id: Optional[int]
    faction_id: Optional[int]
    status: OfferStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OfferAccept(BaseModel):
    buyer_user_id: Optional[int] = None
    buyer_faction_id: Optional[int] = None
    quantity: Optional[int] = None

    class Config:
        json_schema_extra = {"example": {"buyer_user_id": 12, "quantity": 5}}


class OfferAcceptOut(BaseModel):
    offer_id: int
    transaction_id: int
    status: str
