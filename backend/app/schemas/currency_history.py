from typing import Optional

from pydantic import BaseModel, ConfigDict

from .base import UTCDatetime


class CurrencyHistoryBase(BaseModel):
    currency_name: str
    actor_user_id: Optional[int] = None
    old_total_in_circulation: int
    new_total_in_circulation: int
    notes: Optional[str] = None


class CurrencyHistoryOut(CurrencyHistoryBase):
    history_id: int
    timestamp: UTCDatetime

    model_config = ConfigDict(from_attributes=True)
