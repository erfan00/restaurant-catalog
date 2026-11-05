export interface User {
  id: number;
  email: string;
  full_name: string | null;
  oauth_provider: string | null;
  created_at: string;
}

export interface MenuItem {
  id: number;
  restaurant_id: number;
  name: string;
  description: string | null;
  price: string;
  category: string | null;
  created_at: string;
  updated_at: string;
}

export interface Restaurant {
  id: number;
  owner_id: number;
  name: string;
  cuisine: string | null;
  description: string | null;
  address: string | null;
  created_at: string;
  updated_at: string;
}

export interface RestaurantWithMenu extends Restaurant {
  menu_items: MenuItem[];
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface ApiErrorBody {
  detail?: string | { msg: string; loc: (string | number)[] }[];
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}
