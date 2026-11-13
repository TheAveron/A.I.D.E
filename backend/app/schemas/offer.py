from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from ..misc import OfferStatus, OfferType
from .base import INT32_MAX, MAX_PRICE, PartialUpdate, UTCDatetime


class OfferBase(BaseModel):
    offer_type: OfferType
    item_description: str
    currency_name: str
    price_per_unit: float
    quantity: int
    init_quantity: int = 0
    allowed_parties: Optional[list[int]] = Field(None, max_length=1000)


class OfferCreate(OfferBase):
    # Input-only constraints: they must not live on OfferBase, which is also
    # the base of OfferOut (a closed offer legitimately has quantity == 0).
    item_description: str = Field(..., min_length=1, max_length=255)
    price_per_unit: float = Field(..., gt=0, le=MAX_PRICE, allow_inf_nan=False)
    quantity: int = Field(..., gt=0, le=INT32_MAX)
    user_id: Optional[int] = None
    faction_id: Optional[int] = None


class OfferUpdate(PartialUpdate):
    non_nullable = ("status", "price_per_unit", "quantity")

    status: Optional[OfferStatus] = None
    price_per_unit: Optional[float] = Field(
        None, gt=0, le=MAX_PRICE, allow_inf_nan=False
    )
    quantity: Optional[int] = Field(None, gt=0, le=INT32_MAX)
    allowed_parties: Optional[list[int]] = Field(None, max_length=1000)


class OfferOut(OfferBase):
    offer_id: int
    user_id: Optional[int]
    faction_id: Optional[int]
    status: OfferStatus
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class OfferAccept(BaseModel):
    buyer_user_id: Optional[int] = None
    buyer_faction_id: Optional[int] = None
    quantity: Optional[int] = Field(None, gt=0, le=INT32_MAX)

    model_config = ConfigDict(
        json_schema_extra={"example": {"buyer_user_id": 12, "quantity": 5}}
    )


class OfferAcceptOut(BaseModel):
    offer_id: int
    transaction_id: int
    status: str
