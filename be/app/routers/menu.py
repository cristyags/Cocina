from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.deps import get_current_user
from app.schemas.menu_item import MenuItemCreate, MenuItemOut, MenuItemUpdate
from app.services import menu_service


router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("/", response_model=list[MenuItemOut])
async def get_public_menu(db: Session = Depends(get_db)):
    return menu_service.get_menu(db)


@router.get("/all", response_model=list[MenuItemOut])
async def get_management_menu(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return menu_service.get_full_menu(db)


@router.post("/", response_model=MenuItemOut, status_code=status.HTTP_201_CREATED)
async def add_menu_item(
    data: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return menu_service.add_item(db, data)


@router.patch("/{item_id}", response_model=MenuItemOut)
async def update_menu_item(
    item_id: int,
    data: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = menu_service.update_item(db, item_id, data)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item


@router.patch("/{item_id}/toggle", response_model=MenuItemOut)
async def toggle_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = menu_service.toggle_availability(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item
