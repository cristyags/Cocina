from sqlalchemy.orm import Session

from app.repositories import menu_item_repo, order_repo
from app.schemas.order import OrderCreate
from app.services import kitchen_grpc_client, notification_service


def place_order(db: Session, waiter_id: int, data: OrderCreate):
    items_dicts: list[dict] = []
    for item in data.items:
        menu_item = menu_item_repo.get_by_id(db, item.menu_item_id)
        if menu_item is None or not menu_item.is_available:
            return None
        items_dicts.append(
            {
                "menu_item_id": menu_item.id,
                "quantity": item.quantity,
                "unit_price": menu_item.price,
                "notes": item.notes,
            }
        )

    order = order_repo.create(
        db,
        waiter_id=waiter_id,
        table_number=data.table_number,
        notes=data.notes,
        items=items_dicts,
    )

    accepted = kitchen_grpc_client.submit_order(order.id, order.table_number)
    if not accepted:
        db.delete(order)
        db.commit()
        return None

    notification_service.send(
        db,
        user_id=waiter_id,
        title="Orden recibida en cocina",
        message=f"La orden de la mesa {order.table_number} fue recibida correctamente en cocina.",
        ntype="order_received",
        related_order_id=order.id,
    )
    return order


def get_my_orders(db: Session, waiter_id: int):
    return order_repo.get_by_waiter(db, waiter_id)


def get_all_orders(db: Session):
    return order_repo.get_all(db)


def update_order_status(db: Session, order_id: int, requesting_user_id: int, new_status: str):
    order = order_repo.get_by_id(db, order_id)
    if order is None:
        return None

    success = kitchen_grpc_client.update_order_status(order_id, new_status)
    if not success:
        return None

    updated = order_repo.update_status(db, order, new_status)

    if new_status == "ready":
        notification_service.send(
            db,
            user_id=updated.waiter_id,
            title="Orden lista",
            message=f"La orden de la mesa {updated.table_number} está lista.",
            ntype="order_ready",
            related_order_id=updated.id,
        )
    elif new_status == "cancelled":
        notification_service.send(
            db,
            user_id=updated.waiter_id,
            title="Orden cancelada",
            message=f"La orden de la mesa {updated.table_number} fue cancelada.",
            ntype="order_cancelled",
            related_order_id=updated.id,
        )

    return updated
