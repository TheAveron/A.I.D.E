from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(UserCreate):
    pass


class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        from_attributes = True
