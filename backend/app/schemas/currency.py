from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CurrencyBase(BaseModel):
    name: str = Field(..., max_length=50)
    symbol: Optional[str] = Field(None, max_length=10)
    faction_id: Optional[int] = None


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(BaseModel):
    symbol: Optional[str] = Field(None, max_length=10)
    faction_id: Optional[int] = None


class CurrencyOut(CurrencyBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attribute = True
