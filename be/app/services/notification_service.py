import asyncio

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.repositories import notification_repo


_connections: dict[int, WebSocket] = {}


def register_ws(user_id: int, websocket: WebSocket):
    _connections[user_id] = websocket


def unregister_ws(user_id: int):
    _connections.pop(user_id, None)


async def push(user_id: int, payload_dict: dict):
    websocket = _connections.get(user_id)
    if websocket is not None:
        await websocket.send_json(payload_dict)


def send(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    ntype: str,
    related_order_id: int | None = None,
):
    notification = notification_repo.create(
        db,
        user_id=user_id,
        title=title,
        message=message,
        ntype=ntype,
        related_order_id=related_order_id,
    )
    payload = {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.type,
        "related_order_id": notification.related_order_id,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }
    try:
        asyncio.ensure_future(push(user_id, payload))
    except RuntimeError:
        pass
    return notification


def get_user_notifications(db: Session, user_id: int):
    return notification_repo.get_for_user(db, user_id)
