from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TransactionBase(BaseModel):
    offer_id: int
    buyer_user_id: Optional[int] = None
    buyer_faction_id: Optional[int] = None
    amount: float
    currency_name: str


class TransactionCreate(TransactionBase):
    pass


class TransactionOut(TransactionBase):
    transaction_id: int
    timestamp: datetime

    class Config:
        from_attributes = True
