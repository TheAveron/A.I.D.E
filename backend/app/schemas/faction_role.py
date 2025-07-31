from typing import Dict, Optional

from pydantic import BaseModel


class FactionRoleBase(BaseModel):
    name: str
    permissions: Optional[Dict[str, bool]] = None


class FactionRoleCreate(FactionRoleBase):
    faction_id: int


class FactionRoleOut(FactionRoleBase):
    rrolde_id: int
    faction_id: int

    class Config:
        from_attributes = True
