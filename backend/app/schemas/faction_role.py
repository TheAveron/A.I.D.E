from typing import Optional

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    name: str = Field(..., max_length=50)
    description: Optional[str] = None

    accept_offers: bool = False
    create_offers: bool = False
    manage_funds: bool = False
    handle_members: bool = False
    manage_roles: bool = False
    manage_docs: bool = False
    view_transactions: bool = False


class RoleCreate(RoleBase):
    faction_id: int


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    accept_offers: Optional[bool] = None
    create_offers: Optional[bool] = None
    manage_funds: Optional[bool] = None
    handle_members: Optional[bool] = None
    manage_roles: Optional[bool] = None
    manage_docs: Optional[bool] = None
    view_transactions: Optional[bool] = None


class RoleOut(RoleBase):
    role_id: int
    faction_id: int

    class Config:
        from_attributes = True
