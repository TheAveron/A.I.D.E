from typing import Optional

from pydantic import BaseModel, Field

from .base import MAX_DESCRIPTION_LENGTH, PartialUpdate, UTCDatetime


class FactionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class FactionCreate(FactionBase):
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)


class FactionOut(FactionBase):
    faction_id: int
    created_at: UTCDatetime
    is_approved: bool

    class Config:
        from_attributes = True


class FactionUpdate(PartialUpdate):
    non_nullable = ("name", "is_approved")

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    is_approved: Optional[bool] = None
