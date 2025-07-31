from typing import Optional

from pydantic import BaseModel


class FactionBase(BaseModel):
    name: str
    description: Optional[str] = None
    currency_name: Optional[str] = None
    currency_amount: Optional[int] = None


class FactionCreate(FactionBase):
    pass


class FactionOut(FactionBase):
    faction_id: int
    is_approved: bool

    class Config:
        from_attributes = True


class FactionUpdate(FactionBase):
    pass  # All optional for update
