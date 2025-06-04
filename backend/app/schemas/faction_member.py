from pydantic import BaseModel


class FactionMemberBase(BaseModel):
    user_id: int
    faction_id: int
    role_id: int


class FactionMemberCreate(FactionMemberBase):
    pass


class FactionMemberOut(FactionMemberBase):
    id: int

    class Config:
        from_attributes = True
