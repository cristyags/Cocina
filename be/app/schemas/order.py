from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(default=1, ge=1)
    notes: str | None = None


class OrderCreate(BaseModel):
    table_number: int
    notes: str | None = None
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: Literal["preparing", "ready", "delivered", "cancelled"]


class OrderItemOut(BaseModel):
    id: int
    order_id: int
    menu_item_id: int
    quantity: int
    unit_price: Decimal
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    table_number: int
    waiter_id: int
    status: str
    notes: str | None = None
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemOut]

    model_config = ConfigDict(from_attributes=True)
