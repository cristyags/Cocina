from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.menu_item import MenuItem


def get_all(db: Session) -> list[MenuItem]:
    return list(db.scalars(select(MenuItem).order_by(MenuItem.category, MenuItem.name)).all())


def get_available(db: Session) -> list[MenuItem]:
    stmt = (
        select(MenuItem)
        .where(MenuItem.is_available.is_(True))
        .order_by(MenuItem.category, MenuItem.name)
    )
    return list(db.scalars(stmt).all())


def get_by_id(db: Session, item_id: int) -> MenuItem | None:
    return db.scalar(select(MenuItem).where(MenuItem.id == item_id))


def create(db: Session, data_dict: dict) -> MenuItem:
    item = MenuItem(**data_dict)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update(db: Session, item: MenuItem, data_dict: dict) -> MenuItem:
    for key, value in data_dict.items():
        if value is not None:
            setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def toggle_availability(db: Session, item: MenuItem) -> MenuItem:
    item.is_available = not item.is_available
    db.commit()
    db.refresh(item)
    return item
