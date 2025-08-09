from pydantic import BaseModel


class Auth(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str

    class Config:
        from_attributes = True
