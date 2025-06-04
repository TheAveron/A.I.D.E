from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    faction_id = Column(Integer, ForeignKey(column="factions.id"), nullable=True)
    faction = relationship("Faction", back_populates="users")

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    role = relationship("Role", back_populates="users")

    offers = relationship("Offer", back_populates="user")

    def __repr__(self):
        return f"<User(username={self.username}, faction={self.faction.name if self.faction else None})>"
