"""Restaurant CRUD endpoints.

Read endpoints are public. Create requires authentication (the creator
becomes the owner). Update/delete require authentication AND ownership,
enforced in `_get_owned_restaurant_or_403`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user
from app.models.restaurant import Restaurant
from app.models.user import User
from app.schemas.restaurant import (
    RestaurantCreate,
    RestaurantRead,
    RestaurantReadWithMenu,
    RestaurantUpdate,
)
from app.services.restaurant_service import (
    DuplicateRestaurantError,
    create_restaurant,
    delete_restaurant,
    get_restaurant,
    list_restaurants,
    update_restaurant,
)

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


async def get_restaurant_or_404(db: AsyncSession, restaurant_id: int) -> Restaurant:
    restaurant = await get_restaurant(db, restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant


async def get_owned_restaurant(
    restaurant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Restaurant:
    """Dependency: 404 if missing, 401 if not authenticated (handled by
    get_current_user), 403 if authenticated but not the owner."""
    restaurant = await get_restaurant_or_404(db, restaurant_id)
    if restaurant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this restaurant",
        )
    return restaurant


@router.get("", response_model=list[RestaurantRead])
async def list_restaurants_endpoint(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> list[Restaurant]:
    return await list_restaurants(db, skip=skip, limit=limit)


@router.get("/{restaurant_id}", response_model=RestaurantReadWithMenu)
async def get_restaurant_endpoint(
    restaurant_id: int, db: AsyncSession = Depends(get_db)
) -> Restaurant:
    return await get_restaurant_or_404(db, restaurant_id)


@router.post("", response_model=RestaurantRead, status_code=status.HTTP_201_CREATED)
async def create_restaurant_endpoint(
    payload: RestaurantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Restaurant:
    try:
        return await create_restaurant(db, payload, owner_id=current_user.id)
    except DuplicateRestaurantError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A restaurant named '{exc}' already exists",
        ) from exc


@router.put("/{restaurant_id}", response_model=RestaurantRead)
async def update_restaurant_endpoint(
    payload: RestaurantUpdate,
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: AsyncSession = Depends(get_db),
) -> Restaurant:
    try:
        return await update_restaurant(db, restaurant, payload)
    except DuplicateRestaurantError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A restaurant named '{exc}' already exists",
        ) from exc


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_restaurant_endpoint(
    restaurant: Restaurant = Depends(get_owned_restaurant),
    db: AsyncSession = Depends(get_db),
) -> None:
    await delete_restaurant(db, restaurant)
