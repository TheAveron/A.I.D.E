from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FactionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    currency_name: Optional[str] = Field(None, max_length=50)
    currency_amount: float = 0.0
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
    currency_name: Optional[str] = Field(None, max_length=50)
    currency_amount: Optional[float] = None
    is_approved: Optional[bool] = None
