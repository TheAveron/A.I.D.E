from pydantic import BaseModel, ConfigDict


class Auth(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str

    model_config = ConfigDict(from_attributes=True)
