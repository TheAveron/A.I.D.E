from typing import Optional

from pydantic import BaseModel, Field

from .base import INT32_MAX, PartialUpdate, UTCDatetime


class CurrencyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    symbol: Optional[str] = Field(None, max_length=10)
    total_in_circulation: int = Field(
        0,
        ge=0,
        le=INT32_MAX,
        description="Total amount of currency currently in circulation",
    )


class CurrencyCreate(CurrencyBase):
    # The faction that creates the currency becomes its (first) issuer
    faction_id: int


class CurrencyUpdate(PartialUpdate):
    non_nullable = ("name", "total_in_circulation")

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    symbol: Optional[str] = Field(None, max_length=10)
    total_in_circulation: Optional[int] = Field(
        None, ge=0, le=INT32_MAX, description="Updated total in circulation"
    )
    # Not stored on the currency: kept in the audit entry of the change.
    notes: Optional[str] = Field(
        None, max_length=500, description="Why the total changed"
    )


class CurrencyFactionOut(BaseModel):
    """A faction using a currency."""

    faction_id: int
    faction_name: Optional[str] = None
    is_issuer: bool
    joined_at: UTCDatetime


class CurrencyPublic(BaseModel):
    """What any logged-in user may know about a currency.

    The declared total in circulation is only meant for the factions that use
    it.
    """

    currency_id: int
    name: str
    symbol: Optional[str] = None
    factions: list[CurrencyFactionOut] = []
    # Whether the caller may change the currency (issuer manager, money admin)
    can_manage: bool = False


class CurrencyOut(CurrencyPublic):
    total_in_circulation: int
    created_at: UTCDatetime
    updated_at: UTCDatetime


class CurrencyInvite(BaseModel):
    """An issuer proposes to a faction to use its currency."""

    faction_id: int


class CurrencyLinkRequestOut(BaseModel):
    request_id: int
    currency_id: int
    currency_name: Optional[str] = None
    faction_id: int
    faction_name: Optional[str] = None
    kind: str  # "REQUEST" | "INVITATION"
    status: str
    created_by_user_id: Optional[int] = None
    created_at: UTCDatetime

    model_config = {"from_attributes": True}
