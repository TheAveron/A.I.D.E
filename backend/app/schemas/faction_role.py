from typing import Optional

from pydantic import BaseModel, Field

from .base import MAX_DESCRIPTION_LENGTH, PartialUpdate


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

    accept_offers: bool = False
    create_offers: bool = False
    manage_funds: bool = False
    handle_members: bool = False
    manage_roles: bool = False
    manage_docs: bool = False
    view_transactions: bool = False


class RoleCreate(RoleBase):
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    faction_id: int


class RoleUpdate(PartialUpdate):
    non_nullable = (
        "name",
        "accept_offers",
        "create_offers",
        "manage_funds",
        "handle_members",
        "manage_roles",
        "manage_docs",
        "view_transactions",
    )

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)

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
