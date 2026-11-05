"""Business logic for MenuItem CRUD (nested under a Restaurant)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import MenuItem
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate


class DuplicateMenuItemError(Exception):
    pass


async def list_menu_items(db: AsyncSession, restaurant_id: int) -> list[MenuItem]:
    result = await db.execute(
        select(MenuItem).where(MenuItem.restaurant_id == restaurant_id).order_by(MenuItem.id)
    )
    return list(result.scalars().all())


async def get_menu_item(db: AsyncSession, restaurant_id: int, item_id: int) -> MenuItem | None:
    result = await db.execute(
        select(MenuItem).where(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id)
    )
    return result.scalar_one_or_none()


async def create_menu_item(
    db: AsyncSession, restaurant_id: int, payload: MenuItemCreate
) -> MenuItem:
    item = MenuItem(**payload.model_dump(), restaurant_id=restaurant_id)
    db.add(item)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DuplicateMenuItemError(payload.name) from exc
    await db.refresh(item)
    return item


async def update_menu_item(db: AsyncSession, item: MenuItem, payload: MenuItemUpdate) -> MenuItem:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(item, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DuplicateMenuItemError(payload.name or "") from exc
    await db.refresh(item)
    return item


async def delete_menu_item(db: AsyncSession, item: MenuItem) -> None:
    await db.delete(item)
    await db.commit()
