from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator

from ..misc import OfferStatus, OfferType
from .base import INT32_MAX, MAX_PRICE, PartialUpdate, UTCDatetime

# How far ahead an offer may be set to expire
MAX_EXPIRY = timedelta(days=366)


def _naive_utc_in_the_future(value: Optional[datetime]) -> Optional[datetime]:
    """An expiry as the naive UTC the database stores; None means "never"."""
    if value is None:
        return None
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if value <= now:
        raise ValueError("The expiry must be in the future")
    if value - now > MAX_EXPIRY:
        raise ValueError("The expiry can't be more than a year away")
    return value


class OfferBase(BaseModel):
    offer_type: OfferType
    item_description: str
    currency_name: str
    price_per_unit: float
    quantity: int
    init_quantity: int = 0
    allowed_user_ids: Optional[list[PositiveInt]] = Field(None, max_length=200)
    allowed_faction_ids: Optional[list[PositiveInt]] = Field(None, max_length=200)


class OfferCreate(OfferBase):
    # Input-only constraints: they must not live on OfferBase, which is also
    # the base of OfferOut (a closed offer legitimately has quantity == 0).
    item_description: str = Field(..., min_length=1, max_length=255)
    price_per_unit: float = Field(..., gt=0, le=MAX_PRICE, allow_inf_nan=False)
    quantity: int = Field(..., gt=0, le=INT32_MAX)
    user_id: Optional[int] = None
    faction_id: Optional[int] = None
    # Optional: the open offer is cancelled after this moment
    expires_at: Optional[datetime] = None

    _check_expiry = field_validator("expires_at")(_naive_utc_in_the_future)


class OfferUpdate(PartialUpdate):
    non_nullable = ("status", "price_per_unit", "quantity")

    status: Optional[OfferStatus] = None
    price_per_unit: Optional[float] = Field(
        None, gt=0, le=MAX_PRICE, allow_inf_nan=False
    )
    quantity: Optional[int] = Field(None, gt=0, le=INT32_MAX)
    allowed_user_ids: Optional[list[PositiveInt]] = Field(None, max_length=200)
    allowed_faction_ids: Optional[list[PositiveInt]] = Field(None, max_length=200)
    # null clears the expiry
    expires_at: Optional[datetime] = None

    _check_expiry = field_validator("expires_at")(_naive_utc_in_the_future)


class OfferOut(OfferBase):
    offer_id: int
    currency_id: int
    user_id: Optional[int]
    faction_id: Optional[int]
    is_private: bool = False
    expires_at: Optional[UTCDatetime] = None
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
