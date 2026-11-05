import { useState } from "react";
import type { FormEvent } from "react";

import type { MenuItem } from "../types";

interface MenuItemFormValues {
  name: string;
  price: string;
  description: string;
  category: string;
}

interface MenuItemFormProps {
  initial?: MenuItem;
  submitLabel: string;
  onSubmit: (values: MenuItemFormValues) => Promise<void>;
  onCancel?: () => void;
}

export default function MenuItemForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}: MenuItemFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [price, setPrice] = useState(initial?.price ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [category, setCategory] = useState(initial?.category ?? "");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit({ name, price, description, category });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="entity-form inline-form" onSubmit={handleSubmit}>
      <label>
        Name *
        <input value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label>
        Price *
        <input
          type="number"
          min="0.01"
          step="0.01"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          required
        />
      </label>
      <label>
        Category
        <input value={category} onChange={(e) => setCategory(e.target.value)} />
      </label>
      <label>
        Description
        <input value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>
      {error && <p className="error">{error}</p>}
      <div className="form-actions">
        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : submitLabel}
        </button>
        {onCancel && (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
