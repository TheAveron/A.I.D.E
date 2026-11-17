"""Creating notifications.

None of these commit: a notification belongs to the transaction of the event
it reports, so it exists exactly when the event does.
"""

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from ..database import Notification, Role, User
from ..misc import FactionPermission
from .preferences import wants_notification

# The oldest ones go once a user has this many.
MAX_PER_USER = 100


def notify(
    db: Session,
    user_id: int,
    kind: str,
    message: str,
    link: Optional[str] = None,
) -> Optional[Notification]:
    """Tell a user something, unless they switched this kind off."""
    if not wants_notification(db, user_id, kind):
        return None
    notification = Notification(
        user_id=user_id, kind=kind, message=message[:300], link=link
    )
    db.add(notification)
    return notification


def notify_many(
    db: Session,
    user_ids: Iterable[int],
    kind: str,
    message: str,
    link: Optional[str] = None,
) -> None:
    for user_id in dict.fromkeys(user_ids):
        notify(db, user_id, kind, message, link)


def members_with_permission(
    db: Session, faction_id: int, permission: FactionPermission
) -> list[int]:
    """The members of a faction whose role holds `permission`."""
    return [
        user_id
        for (user_id,) in db.query(User.user_id)
        .join(Role, User.role_id == Role.role_id)
        .filter(
            User.faction_id == faction_id,
            Role.faction_id == faction_id,
            getattr(Role, permission.value).is_(True),
        )
    ]


def prune(db: Session, user_id: int) -> None:
    """Keep a user's newest MAX_PER_USER notifications."""
    db.flush()
    old = (
        db.query(Notification.notification_id)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc(), Notification.notification_id.desc())
        .offset(MAX_PER_USER)
        .all()
    )
    if old:
        db.query(Notification).filter(
            Notification.notification_id.in_([i for (i,) in old])
        ).delete(synchronize_session=False)
