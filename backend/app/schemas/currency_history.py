from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CurrencyHistoryBase(BaseModel):
    currency_name: str
    actor_user_id: Optional[int] = None
    old_total_in_circulation: int
    new_total_in_circulation: int
    notes: Optional[str] = None


class CurrencyHistoryOut(CurrencyHistoryBase):
    history_id: int
    timestamp: datetime

    class Config:
        from_attributes = True
