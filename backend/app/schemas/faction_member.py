from pydantic import BaseModel, ConfigDict


class FactionMemberBase(BaseModel):
    user_id: int
    faction_id: int
    role_id: int


class FactionMemberCreate(FactionMemberBase):
    pass


class FactionMemberOut(FactionMemberBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
