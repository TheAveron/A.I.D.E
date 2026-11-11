from typing import Optional

from pydantic import BaseModel, Field

from .base import PartialUpdate, UTCDatetime


class FactionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class FactionCreate(FactionBase):
    pass


class FactionOut(FactionBase):
    faction_id: int
    created_at: UTCDatetime
    is_approved: bool

    class Config:
        from_attributes = True


class FactionUpdate(PartialUpdate):
    non_nullable = ("name", "is_approved")

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_approved: Optional[bool] = None
