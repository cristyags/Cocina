from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification


def create(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    ntype: str,
    related_order_id: int | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=ntype,
        related_order_id=related_order_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_for_user(db: Session, user_id: int) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def mark_read(db: Session, notification_id: int, user_id: int) -> Notification | None:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    if notification is None:
        return None
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
