from typing import Optional

from pydantic import BaseModel, ConfigDict

from .base import UTCDatetime


class CurrencyHistoryBase(BaseModel):
    currency_id: int
    # The current name (the entry follows the currency through renames)
    currency_name: Optional[str] = None
    actor_user_id: Optional[int] = None
    old_total_in_circulation: int
    new_total_in_circulation: int
    notes: Optional[str] = None


class CurrencyHistoryOut(CurrencyHistoryBase):
    history_id: int
    timestamp: UTCDatetime

    model_config = ConfigDict(from_attributes=True)
