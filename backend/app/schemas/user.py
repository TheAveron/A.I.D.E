from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserUpdate(UserBase):
    pass


class UserLogin(UserBase):
    pass


class UserCreate(UserBase):
    is_admin: bool = False


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        from_attributes = True
