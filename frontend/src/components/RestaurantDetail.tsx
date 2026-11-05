import { useState } from "react";

import { api } from "../api";
import { useAuth } from "../useAuth";
import type { MenuItem, RestaurantWithMenu } from "../types";
import MenuItemForm from "./MenuItemForm";
import RestaurantForm from "./RestaurantForm";

interface RestaurantDetailProps {
  restaurant: RestaurantWithMenu;
  onChanged: () => void;
  onDeleted: () => void;
}

export default function RestaurantDetail({
  restaurant,
  onChanged,
  onDeleted,
}: RestaurantDetailProps) {
  const { user } = useAuth();
  const [editing, setEditing] = useState(false);
  const [addingItem, setAddingItem] = useState(false);
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const isOwner = user !== null && user.id === restaurant.owner_id;

  async function handleDeleteRestaurant() {
    if (!window.confirm(`Delete "${restaurant.name}" and all of its menu items?`)) {
      return;
    }
    setActionError(null);
    try {
      await api.deleteRestaurant(restaurant.id);
      onDeleted();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to delete restaurant");
    }
  }

  async function handleDeleteItem(item: MenuItem) {
    if (!window.confirm(`Delete "${item.name}"?`)) {
      return;
    }
    setActionError(null);
    try {
      await api.deleteMenuItem(restaurant.id, item.id);
      onChanged();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to delete menu item");
    }
  }

  return (
    <div className="card restaurant-detail">
      {editing ? (
        <RestaurantForm
          initial={restaurant}
          submitLabel="Save changes"
          onCancel={() => setEditing(false)}
          onSubmit={async (values) => {
            await api.updateRestaurant(restaurant.id, values);
            setEditing(false);
            onChanged();
          }}
        />
      ) : (
        <>
          <div className="detail-header">
            <div>
              <h2>{restaurant.name}</h2>
              {restaurant.cuisine && <p className="muted">{restaurant.cuisine}</p>}
            </div>
            {isOwner && (
              <div className="owner-actions">
                <button type="button" onClick={() => setEditing(true)}>
                  Edit
                </button>
                <button type="button" className="danger" onClick={handleDeleteRestaurant}>
                  Delete
                </button>
              </div>
            )}
          </div>
          {restaurant.description && <p>{restaurant.description}</p>}
          {restaurant.address && <p className="muted">{restaurant.address}</p>}
        </>
      )}

      {actionError && <p className="error">{actionError}</p>}

      <h3>Menu</h3>
      {restaurant.menu_items.length === 0 && <p className="empty">No menu items yet.</p>}
      <ul className="menu-item-list">
        {restaurant.menu_items.map((item) =>
          editingItemId === item.id ? (
            <li key={item.id}>
              <MenuItemForm
                initial={item}
                submitLabel="Save item"
                onCancel={() => setEditingItemId(null)}
                onSubmit={async (values) => {
                  await api.updateMenuItem(restaurant.id, item.id, values);
                  setEditingItemId(null);
                  onChanged();
                }}
              />
            </li>
          ) : (
            <li key={item.id} className="menu-item">
              <div>
                <span className="menu-item-name">{item.name}</span>
                {item.category && <span className="menu-item-category">{item.category}</span>}
                {item.description && <p className="muted">{item.description}</p>}
              </div>
              <div className="menu-item-right">
                <span className="menu-item-price">${item.price}</span>
                {isOwner && (
                  <div className="owner-actions">
                    <button type="button" onClick={() => setEditingItemId(item.id)}>
                      Edit
                    </button>
                    <button type="button" className="danger" onClick={() => handleDeleteItem(item)}>
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </li>
          ),
        )}
      </ul>

      {isOwner && !addingItem && (
        <button type="button" onClick={() => setAddingItem(true)}>
          + Add menu item
        </button>
      )}
      {isOwner && addingItem && (
        <MenuItemForm
          submitLabel="Add item"
          onCancel={() => setAddingItem(false)}
          onSubmit={async (values) => {
            await api.createMenuItem(restaurant.id, values);
            setAddingItem(false);
            onChanged();
          }}
        />
      )}
    </div>
  );
}
