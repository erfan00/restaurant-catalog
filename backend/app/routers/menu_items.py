"""MenuItem CRUD endpoints, nested under /restaurants/{restaurant_id}.

Read endpoints are public. Write endpoints require the caller to own the
parent restaurant (ownership is on the restaurant, not the menu item).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant
from app.routers.restaurants import get_owned_restaurant, get_restaurant_or_404
from app.schemas.menu_item import MenuItemCreate, MenuItemRead, MenuItemUpdate
from app.services.menu_item_service import (
    DuplicateMenuItemError,
    create_menu_item,
    delete_menu_item,
    get_menu_item,
    list_menu_items,
    update_menu_item,
)

router = APIRouter(prefix="/restaurants/{restaurant_id}/menu-items", tags=["menu-items"])


async def _get_menu_item_or_404(db: AsyncSession, restaurant_id: int, item_id: int) -> MenuItem:
    item = await get_menu_item(db, restaurant_id, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
    return item


@router.get("", response_model=list[MenuItemRead])
async def list_menu_items_endpoint(
    restaurant_id: int, db: AsyncSession = Depends(get_db)
) -> list[MenuItem]:
    await get_restaurant_or_404(db, restaurant_id)
    return await list_menu_items(db, restaurant_id)


@router.get("/{item_id}", response_model=MenuItemRead)
async def get_menu_item_endpoint(
    restaurant_id: int, item_id: int, db: AsyncSession = Depends(get_db)
) -> MenuItem:
    await get_restaurant_or_404(db, restaurant_id)
    return await _get_menu_item_or_404(db, restaurant_id, item_id)


@router.post("", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
async def create_menu_item_endpoint(
    payload: MenuItemCreate,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: AsyncSession = Depends(get_db),
) -> MenuItem:
    try:
        return await create_menu_item(db, restaurant.id, payload)
    except DuplicateMenuItemError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A menu item named '{exc}' already exists for this restaurant",
        ) from exc


@router.put("/{item_id}", response_model=MenuItemRead)
async def update_menu_item_endpoint(
    item_id: int,
    payload: MenuItemUpdate,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: AsyncSession = Depends(get_db),
) -> MenuItem:
    item = await _get_menu_item_or_404(db, restaurant.id, item_id)
    try:
        return await update_menu_item(db, item, payload)
    except DuplicateMenuItemError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A menu item named '{exc}' already exists for this restaurant",
        ) from exc


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_menu_item_endpoint(
    item_id: int,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: AsyncSession = Depends(get_db),
) -> None:
    item = await _get_menu_item_or_404(db, restaurant.id, item_id)
    await delete_menu_item(db, item)
