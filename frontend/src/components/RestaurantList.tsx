import type { Restaurant } from "../types";

interface RestaurantListProps {
  restaurants: Restaurant[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export default function RestaurantList({ restaurants, selectedId, onSelect }: RestaurantListProps) {
  if (restaurants.length === 0) {
    return <p className="empty">No restaurants yet. Be the first to add one.</p>;
  }

  return (
    <ul className="restaurant-list">
      {restaurants.map((r) => (
        <li key={r.id}>
          <button
            type="button"
            className={r.id === selectedId ? "restaurant-item active" : "restaurant-item"}
            onClick={() => onSelect(r.id)}
          >
            <span className="restaurant-name">{r.name}</span>
            {r.cuisine && <span className="restaurant-cuisine">{r.cuisine}</span>}
          </button>
        </li>
      ))}
    </ul>
  );
}
