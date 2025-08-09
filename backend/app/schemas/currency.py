from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CurrencyBase(BaseModel):
    name: str = Field(..., max_length=50)
    symbol: Optional[str] = Field(None, max_length=10)
    faction_id: int
    total_in_circulation: Optional[int] = Field(
        0, ge=0, description="Total amount of currency currently in circulation"
    )


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(BaseModel):
    name: str = Field(..., max_length=50)
    symbol: Optional[str] = Field(None, max_length=10)
    total_in_circulation: Optional[int] = Field(
        None, ge=0, description="Updated total in circulation"
    )


class CurrencyOut(CurrencyBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attribute = True
