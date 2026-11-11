from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..misc import OfferStatus, OfferType


class OfferBase(BaseModel):
    offer_type: OfferType
    item_description: str
    currency_name: str
    price_per_unit: float
    quantity: int
    init_quantity: int = 0
    allowed_parties: Optional[list[int]] = None


class OfferCreate(OfferBase):
    # Input-only constraints: they must not live on OfferBase, which is also
    # the base of OfferOut (a closed offer legitimately has quantity == 0).
    item_description: str = Field(..., min_length=1, max_length=255)
    price_per_unit: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    user_id: Optional[int] = None
    faction_id: Optional[int] = None


class OfferUpdate(BaseModel):
    status: Optional[OfferStatus] = None
    price_per_unit: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, gt=0)
    allowed_parties: Optional[list[int]] = None


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
    quantity: Optional[int] = Field(None, gt=0)

    class Config:
        json_schema_extra = {"example": {"buyer_user_id": 12, "quantity": 5}}


class OfferAcceptOut(BaseModel):
    offer_id: int
    transaction_id: int
    status: str
