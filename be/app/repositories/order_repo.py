from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderItem


def create(
    db: Session,
    waiter_id: int,
    table_number: int,
    notes: str | None,
    items: list[dict],
) -> Order:
    total_amount = sum(item["unit_price"] * item["quantity"] for item in items)
    order = Order(
        waiter_id=waiter_id,
        table_number=table_number,
        notes=notes,
        total_amount=total_amount,
    )
    db.add(order)
    db.flush()

    for entry in items:
        db.add(
            OrderItem(
                order_id=order.id,
                menu_item_id=entry["menu_item_id"],
                quantity=entry["quantity"],
                unit_price=entry["unit_price"],
                notes=entry.get("notes"),
            )
        )

    db.commit()
    db.refresh(order)
    return get_by_id(db, order.id)


def get_by_waiter(db: Session, waiter_id: int) -> list[Order]:
    stmt = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.waiter_id == waiter_id)
        .order_by(Order.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_all(db: Session) -> list[Order]:
    stmt = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
    return list(db.scalars(stmt).all())


def get_by_id(db: Session, order_id: int) -> Order | None:
    stmt = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    return db.scalar(stmt)


def update_status(db: Session, order: Order, new_status: str) -> Order:
    order.status = new_status
    db.commit()
    db.refresh(order)
    return get_by_id(db, order.id)
