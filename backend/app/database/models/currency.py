from sqlalchemy import String, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base


class Currency(Base):
    """
    Represents a tradable currency in the marketplace.
    """

    __tablename__ = "currencies"

    name: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        nullable=False,
        index=True,  # Useful if searched often
    )

    total_in_circulation: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # Relationships
    offers = relationship(
        "Offer", back_populates="currency", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Currency(name={self.name}, total={self.total_in_circulation})>"

    def __str__(self) -> str:
        return (
            f"Currency: {self.name} (Total in circulation: {self.total_in_circulation})"
        )
