from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FactionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_approved: bool = False


class FactionCreate(FactionBase):
    pass


class FactionOut(FactionBase):
    faction_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FactionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_approved: Optional[bool] = None
