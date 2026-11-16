"""An account's preferences, and which notifications they let through."""

from sqlalchemy.orm import Session

from ..database import UserPreferences

THEMES = ("system", "dark", "light")

# Notifications a user can switch off, by category. Anything not listed here
# (a password reset, being removed from a faction, an admin cancelling one of
# your offers...) always arrives: it is about security or about moderation.
OPTIONAL_KINDS: dict[str, frozenset[str]] = {
    "notify_market": frozenset({"offer_accepted", "offer_expired"}),
    "notify_faction": frozenset(
        {
            "join_request",
            "join_accepted",
            "join_refused",
            "role_changed",
            "leadership",
        }
    ),
}


def get_preferences(db: Session, user_id: int) -> UserPreferences:
    """The account's preferences; an unsaved default when it has none yet."""
    row = db.get(UserPreferences, user_id)
    if row is None:
        row = UserPreferences(
            user_id=user_id, theme="dark", notify_market=True, notify_faction=True
        )
    return row


def wants_notification(db: Session, user_id: int, kind: str) -> bool:
    """Whether this user left notifications of this kind switched on."""
    for column, kinds in OPTIONAL_KINDS.items():
        if kind in kinds:
            row = db.get(UserPreferences, user_id)
            return row is None or bool(getattr(row, column))
    return True


def save_preferences(db: Session, user_id: int, changes: dict) -> UserPreferences:
    """Create or update the row (the caller commits)."""
    row = db.get(UserPreferences, user_id)
    if row is None:
        row = UserPreferences(
            user_id=user_id, theme="dark", notify_market=True, notify_faction=True
        )
        db.add(row)
    for name, value in changes.items():
        setattr(row, name, value)
    return row
