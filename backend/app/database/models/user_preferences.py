from sqlalchemy import Boolean, ForeignKey, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class UserPreferences(Base):
    """What an account chose for the site. A row exists once something was
    changed; without one, everything is on and the theme is dark.
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )

    # "dark" | "light" | "system"
    theme: Mapped[str] = mapped_column(
        String(10), nullable=False, default="dark", server_default="dark"
    )

    # Notifications that can be switched off, by category (crud/preferences.py)
    notify_market: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    notify_faction: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
