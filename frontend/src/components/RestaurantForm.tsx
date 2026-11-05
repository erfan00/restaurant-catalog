import { useState } from "react";
import type { FormEvent } from "react";

import type { Restaurant } from "../types";

interface RestaurantFormValues {
  name: string;
  cuisine: string;
  description: string;
  address: string;
}

interface RestaurantFormProps {
  initial?: Restaurant;
  submitLabel: string;
  onSubmit: (values: RestaurantFormValues) => Promise<void>;
  onCancel?: () => void;
}

export default function RestaurantForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}: RestaurantFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [cuisine, setCuisine] = useState(initial?.cuisine ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [address, setAddress] = useState(initial?.address ?? "");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit({ name, cuisine, description, address });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="entity-form" onSubmit={handleSubmit}>
      <label>
        Name *
        <input value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label>
        Cuisine
        <input value={cuisine} onChange={(e) => setCuisine(e.target.value)} />
      </label>
      <label>
        Description
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>
      <label>
        Address
        <input value={address} onChange={(e) => setAddress(e.target.value)} />
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
