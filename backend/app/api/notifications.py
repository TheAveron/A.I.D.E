"""A user's own notifications: nobody reads anybody else's."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core import get_current_user
from ..crud import notification as crud_notification
from ..database import Notification, User, get_db
from ..schemas.notification import NotificationOut, UnreadCount

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The caller's notifications, newest first."""
    crud_notification.prune(db, current_user.user_id)
    db.commit()

    query = db.query(Notification).filter(Notification.user_id == current_user.user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return (
        query.order_by(
            Notification.created_at.desc(), Notification.notification_id.desc()
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/unread_count", response_model=UnreadCount)
def unread_count(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    count = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.user_id,
            Notification.is_read.is_(False),
        )
        .count()
    )
    return UnreadCount(count=count)


@router.post("/read_all", response_model=UnreadCount)
def mark_all_read(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Mark everything as read; answers with the number of unread ones left (0)."""
    db.query(Notification).filter(
        Notification.user_id == current_user.user_id,
        Notification.is_read.is_(False),
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return UnreadCount(count=0)


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.notification_id == notification_id,
            Notification.user_id == current_user.user_id,
        )
        .first()
    )
    if not notification:
        # Somebody else's notification doesn't exist for the caller.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
