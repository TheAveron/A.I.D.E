from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import UTCDatetime

USERNAME_MAX_LENGTH = 50  # users.username is a String(50)
PASSWORD_MAX_BYTES = 72  # bcrypt only looks at the first 72 bytes


class UserLogin(BaseModel):
    """Credentials sent to /auth/login.

    Deliberately lenient: existing accounts must be able to log in whatever
    rules registration enforces today.
    """

    username: str
    password: str


class UserCreate(BaseModel):
    """Registration body: the limits match what the database and bcrypt accept."""

    username: str = Field(..., min_length=1, max_length=USERNAME_MAX_LENGTH)
    password: str = Field(..., min_length=1)

    @field_validator("username")
    @classmethod
    def _username_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Username can't be blank")
        return value

    @field_validator("password")
    @classmethod
    def _password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
            raise ValueError(
                f"Password is too long (at most {PASSWORD_MAX_BYTES} bytes)"
            )
        return value


class UserUpdate(BaseModel):
    role_id: Optional[int] = None
    faction_id: Optional[int] = None


class UserOut(BaseModel):
    user_id: int
    username: str
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserPublic(UserOut):
    """What anyone logged in or not may see about a user: no email."""

    created_at: UTCDatetime

    faction_id: int | None
    role_id: int | None


class UserFull(UserPublic):
    """The account holder's own view (/users/me)."""

    email: str | None
