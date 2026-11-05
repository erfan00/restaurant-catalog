import type { ApiErrorBody, MenuItem, Restaurant, RestaurantWithMenu, Token, User } from "./types";
import { ApiError } from "./types";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "/api";

const TOKEN_STORAGE_KEY = "restaurant_catalog_token";

export function getStoredToken(): string | null {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) {
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

function authHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorBody;
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail)) {
      return body.detail.map((d) => d.msg).join("; ");
    }
  } catch {
    // response wasn't JSON; fall through to generic message
  }
  return `Request failed with status ${response.status}`;
}

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = false, headers, ...rest } = options;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      ...(auth ? authHeaders() : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function jsonBody(body: unknown): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export const api = {
  async register(email: string, password: string): Promise<User> {
    return request<User>("/auth/register", jsonBody({ email, password }));
  },

  async login(email: string, password: string): Promise<Token> {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    return request<Token>("/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
  },

  async me(): Promise<User> {
    return request<User>("/auth/me", { auth: true });
  },

  async listRestaurants(): Promise<Restaurant[]> {
    return request<Restaurant[]>("/restaurants");
  },

  async getRestaurant(id: number): Promise<RestaurantWithMenu> {
    return request<RestaurantWithMenu>(`/restaurants/${id}`);
  },

  async createRestaurant(payload: {
    name: string;
    cuisine?: string;
    description?: string;
    address?: string;
  }): Promise<Restaurant> {
    return request<Restaurant>("/restaurants", { ...jsonBody(payload), auth: true });
  },

  async updateRestaurant(
    id: number,
    payload: Partial<{ name: string; cuisine: string; description: string; address: string }>,
  ): Promise<Restaurant> {
    return request<Restaurant>(`/restaurants/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      auth: true,
    });
  },

  async deleteRestaurant(id: number): Promise<void> {
    await request<void>(`/restaurants/${id}`, { method: "DELETE", auth: true });
  },

  async createMenuItem(
    restaurantId: number,
    payload: { name: string; price: string; description?: string; category?: string },
  ): Promise<MenuItem> {
    return request<MenuItem>(`/restaurants/${restaurantId}/menu-items`, {
      ...jsonBody(payload),
      auth: true,
    });
  },

  async updateMenuItem(
    restaurantId: number,
    itemId: number,
    payload: Partial<{ name: string; price: string; description: string; category: string }>,
  ): Promise<MenuItem> {
    return request<MenuItem>(`/restaurants/${restaurantId}/menu-items/${itemId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      auth: true,
    });
  },

  async deleteMenuItem(restaurantId: number, itemId: number): Promise<void> {
    await request<void>(`/restaurants/${restaurantId}/menu-items/${itemId}`, {
      method: "DELETE",
      auth: true,
    });
  },
};
