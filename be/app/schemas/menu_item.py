from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MenuItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    category: str
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    category: str | None = None
    is_available: bool | None = None


class MenuItemOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: Decimal
    category: str
    is_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
