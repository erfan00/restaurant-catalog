"""Business logic for Restaurant CRUD."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate


class DuplicateRestaurantError(Exception):
    pass


async def list_restaurants(
    db: AsyncSession, *, skip: int = 0, limit: int = 100
) -> list[Restaurant]:
    result = await db.execute(select(Restaurant).order_by(Restaurant.id).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_restaurant(db: AsyncSession, restaurant_id: int) -> Restaurant | None:
    result = await db.execute(
        select(Restaurant)
        .options(selectinload(Restaurant.menu_items))
        .where(Restaurant.id == restaurant_id)
    )
    return result.scalar_one_or_none()


async def create_restaurant(
    db: AsyncSession, payload: RestaurantCreate, owner_id: int
) -> Restaurant:
    restaurant = Restaurant(**payload.model_dump(), owner_id=owner_id)
    db.add(restaurant)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DuplicateRestaurantError(payload.name) from exc
    await db.refresh(restaurant)
    return restaurant


async def update_restaurant(
    db: AsyncSession, restaurant: Restaurant, payload: RestaurantUpdate
) -> Restaurant:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(restaurant, field, value)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise DuplicateRestaurantError(payload.name or "") from exc
    await db.refresh(restaurant)
    return restaurant


async def delete_restaurant(db: AsyncSession, restaurant: Restaurant) -> None:
    await db.delete(restaurant)
    await db.commit()
