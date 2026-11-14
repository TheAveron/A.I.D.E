from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .base import UTCDatetime

MAX_MESSAGE_LENGTH = 500


class JoinRequestCreate(BaseModel):
    faction_id: int
    message: Optional[str] = Field(None, max_length=MAX_MESSAGE_LENGTH)


class JoinRequestOut(BaseModel):
    request_id: int
    user_id: int
    username: str
    faction_id: int
    status: str
    message: Optional[str] = None
    created_at: UTCDatetime
    decided_at: Optional[UTCDatetime] = None

    model_config = ConfigDict(from_attributes=True)
