from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=True)

    faction_id = Column(Integer, ForeignKey("factions.id"), nullable=False)
    faction = relationship("Faction", back_populates="roles")

    users = relationship("User", back_populates="role")

    def __repr__(self):
        return f"<Role(name={self.name}, faction={self.faction.name})>"
