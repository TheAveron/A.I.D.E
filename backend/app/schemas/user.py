from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    role_id: Optional[int] = None
    faction_id: Optional[int] = None


class UserLogin(UserBase):
    pass


class UserCreate(UserBase):
    is_admin: bool = False


class UserOut(BaseModel):
    user_id: int
    username: str
    is_admin: bool

    class Config:
        from_attributes = True


class UserFull(UserOut):
    email: str | None
    created_at: datetime

    faction_id: int | None
    role_id: int | None
