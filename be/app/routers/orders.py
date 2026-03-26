from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.deps import get_current_user
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from app.services import order_service


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = order_service.place_order(db, current_user.id, data)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Some items are unavailable or missing",
        )
    return order


@router.get("/mine", response_model=list[OrderOut])
async def get_my_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return order_service.get_my_orders(db, current_user.id)


@router.get("/", response_model=list[OrderOut])
async def get_all_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return order_service.get_all_orders(db)


@router.patch("/{order_id}/status", response_model=OrderOut)
async def patch_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    order = order_service.update_order_status(db, order_id, current_user.id, data.status)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid status transition",
        )
    return order
