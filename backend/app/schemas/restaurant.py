from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.menu_item import MenuItemRead


class RestaurantBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    cuisine: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    address: str | None = Field(default=None, max_length=255)


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    cuisine: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    address: str | None = Field(default=None, max_length=255)


class RestaurantRead(RestaurantBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime


class RestaurantReadWithMenu(RestaurantRead):
    menu_items: list[MenuItemRead] = Field(default_factory=list)
