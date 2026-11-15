from pydantic import BaseModel, ConfigDict

from ..database import GlobalRoleName
from .base import UTCDatetime


class GlobalRoleOut(BaseModel):
    user_id: int
    username: str
    role: GlobalRoleName
    granted_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)
