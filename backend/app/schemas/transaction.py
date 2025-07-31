from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class TransactionOut(BaseModel):
    transaction_id: int
    offer_id: int
    buyer_id: Optional[int]
    buyer_faction_id: Optional[int]
    amount: Decimal
    currency: str
    timestamp: datetime

    class Config:
        from_attributes = True
