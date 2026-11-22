from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import UTCDatetime
from .currency import CurrencyFactionOut
from .user import PASSWORD_MAX_BYTES


class AuditLogOut(BaseModel):
    log_id: int
    actor_user_id: Optional[int] = None
    actor_name: str
    action: str
    target_type: str
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    detail: Optional[str] = None
    created_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserOut(BaseModel):
    user_id: int
    username: str
    email: Optional[str] = None
    faction_id: Optional[int] = None
    faction_name: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    global_roles: list[str] = []
    created_at: UTCDatetime


class AdminFactionOut(BaseModel):
    faction_id: int
    name: str
    is_approved: bool
    requires_approval: bool
    member_count: int
    created_at: UTCDatetime
    deleted_at: Optional[UTCDatetime] = None


class AdminPasswordReset(BaseModel):
    """Body of POST /admin/users/{id}/password."""

    new_password: str = Field(..., min_length=4)

    @field_validator("new_password")
    @classmethod
    def _fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
            raise ValueError(
                f"Password is too long (at most {PASSWORD_MAX_BYTES} bytes)"
            )
        return value


class AdminReason(BaseModel):
    """Why an admin cancels something: kept in the audit trail and told to the
    people concerned."""

    reason: str = Field(..., min_length=3, max_length=200)

    @field_validator("reason")
    @classmethod
    def _stripped(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Give a reason of at least 3 characters")
        return value


class AdminOfferOut(BaseModel):
    offer_id: int
    offer_type: str
    item_description: str
    currency_name: str
    price_per_unit: float
    quantity: int
    init_quantity: int
    status: str
    is_private: bool
    owner_kind: str  # "user" | "faction"
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    expires_at: Optional[UTCDatetime] = None
    created_at: UTCDatetime


class AdminTransactionOut(BaseModel):
    transaction_id: int
    offer_id: int
    item_description: str
    buyer_name: Optional[str] = None
    seller_name: Optional[str] = None
    amount: float
    currency_name: str
    quantity: Optional[int] = None
    timestamp: UTCDatetime
    cancelled_at: Optional[UTCDatetime] = None
    cancelled_by_name: Optional[str] = None
    cancel_reason: Optional[str] = None


class AdminTransactionCancelled(BaseModel):
    transaction: AdminTransactionOut
    # False when the row predates the recorded quantity: nothing was given back
    quantity_restored: bool
    offer_reopened: bool


class AdminCurrencyOut(BaseModel):
    currency_id: int
    name: str
    symbol: Optional[str] = None
    factions: list[CurrencyFactionOut] = []
    total_in_circulation: int
    created_at: UTCDatetime


class AdminUserState(BaseModel):
    """Read-only dump of an account, to debug what somebody reports."""

    user: AdminUserOut
    token_version: int
    offers_by_status: dict[str, int]
    purchases: int
    sales: int
    unread_notifications: int
    pending_join_request: Optional[str] = None
    trains_owned: int


class AdminRoleState(BaseModel):
    name: str
    member_count: int


class AdminFactionState(BaseModel):
    """Read-only dump of a faction."""

    faction: AdminFactionOut
    description: Optional[str] = None
    leader: Optional[str] = None
    roles: list[AdminRoleState]
    currency: Optional[AdminCurrencyOut] = None
    offers_by_status: dict[str, int]
    pending_join_requests: int
    trains_owned: int
