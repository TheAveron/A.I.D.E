from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import UTCDatetime
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
