import { useCallback, useEffect, useState } from "react";

import { api } from "./api";
import { useAuth } from "./useAuth";
import LoginPanel from "./components/LoginPanel";
import RestaurantDetail from "./components/RestaurantDetail";
import RestaurantForm from "./components/RestaurantForm";
import RestaurantList from "./components/RestaurantList";
import type { Restaurant, RestaurantWithMenu } from "./types";

export default function App() {
  const { user, loading, logout } = useAuth();
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [selected, setSelected] = useState<RestaurantWithMenu | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [listError, setListError] = useState<string | null>(null);

  const refreshList = useCallback(async () => {
    try {
      const data = await api.listRestaurants();
      setRestaurants(data);
      setListError(null);
    } catch (err) {
      setListError(err instanceof Error ? err.message : "Failed to load restaurants");
    }
  }, []);

  const refreshSelected = useCallback(async (id: number) => {
    try {
      const data = await api.getRestaurant(id);
      setSelected(data);
    } catch {
      setSelected(null);
    }
  }, []);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  useEffect(() => {
    if (selectedId !== null) {
      void refreshSelected(selectedId);
    } else {
      setSelected(null);
    }
  }, [selectedId, refreshSelected]);

  function handleSelect(id: number) {
    setSelectedId(id);
    setShowCreateForm(false);
  }

  async function handleChanged() {
    await refreshList();
    if (selectedId !== null) {
      await refreshSelected(selectedId);
    }
  }

  async function handleDeleted() {
    setSelectedId(null);
    await refreshList();
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Restaurant Catalog</h1>
        <div className="header-right">
          {loading ? null : user ? (
            <>
              <span className="welcome">Signed in as {user.email}</span>
              <button type="button" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            <span className="welcome">Browsing as a guest</span>
          )}
        </div>
      </header>

      <main className="app-main">
        <section className="sidebar">
          <div className="sidebar-header">
            <h2>Restaurants</h2>
            {user && (
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm((v) => !v);
                  setSelectedId(null);
                }}
              >
                {showCreateForm ? "Cancel" : "+ New"}
              </button>
            )}
          </div>
          {listError && <p className="error">{listError}</p>}
          <RestaurantList
            restaurants={restaurants}
            selectedId={selectedId}
            onSelect={handleSelect}
          />
        </section>

        <section className="content">
          {showCreateForm && user ? (
            <div className="card">
              <h2>New restaurant</h2>
              <RestaurantForm
                submitLabel="Create restaurant"
                onCancel={() => setShowCreateForm(false)}
                onSubmit={async (values) => {
                  const created = await api.createRestaurant(values);
                  setShowCreateForm(false);
                  await refreshList();
                  setSelectedId(created.id);
                }}
              />
            </div>
          ) : selected ? (
            <RestaurantDetail
              restaurant={selected}
              onChanged={handleChanged}
              onDeleted={handleDeleted}
            />
          ) : (
            <div className="card placeholder">
              <p>Select a restaurant from the list to see its menu.</p>
            </div>
          )}

          {!user && !loading && (
            <div className="auth-area">
              <LoginPanel />
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
