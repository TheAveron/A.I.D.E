from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class Currency(Base):
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    total_in_circulation = Column(
        Float, nullable=True
    )  # For future exchange rate logic

    offers = relationship("Offer", back_populates="currency")
