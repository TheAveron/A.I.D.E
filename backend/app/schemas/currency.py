from typing import Optional

from pydantic import BaseModel, Field

from .base import INT32_MAX, PartialUpdate, UTCDatetime


class CurrencyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    symbol: Optional[str] = Field(None, max_length=10)
    faction_id: int
    total_in_circulation: int = Field(
        0,
        ge=0,
        le=INT32_MAX,
        description="Total amount of currency currently in circulation",
    )


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(PartialUpdate):
    non_nullable = ("name", "total_in_circulation")

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    symbol: Optional[str] = Field(None, max_length=10)
    total_in_circulation: Optional[int] = Field(
        None, ge=0, le=INT32_MAX, description="Updated total in circulation"
    )


class CurrencyPublic(BaseModel):
    """What any logged-in user may know about a faction's currency.

    The declared total in circulation is only meant for the faction itself.
    """

    name: str
    symbol: Optional[str] = None
    faction_id: Optional[int] = None

    model_config = {"from_attributes": True}


class CurrencyOut(CurrencyBase):
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = {"from_attributes": True}
