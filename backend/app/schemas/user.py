from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    password: str


class UserUpdate(UserBase):
    pass


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
