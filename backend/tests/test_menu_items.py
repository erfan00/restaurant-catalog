"""CRUD tests for nested /restaurants/{id}/menu-items."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import register_and_login


def _create_restaurant(
    client: TestClient, headers: dict[str, str], name: str = "Pizza Pit"
) -> dict:
    resp = client.post("/restaurants", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def test_list_menu_items_empty(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner1@example.com")
    restaurant = _create_restaurant(client, headers)
    resp = client.get(f"/restaurants/{restaurant['id']}/menu-items")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_menu_items_for_missing_restaurant_404(client: TestClient) -> None:
    resp = client.get("/restaurants/99999/menu-items")
    assert resp.status_code == 404


def test_create_menu_item_requires_auth(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner2@example.com")
    restaurant = _create_restaurant(client, headers)
    resp = client.post(
        f"/restaurants/{restaurant['id']}/menu-items",
        json={"name": "Margherita", "price": "9.99"},
    )
    assert resp.status_code == 401


def test_owner_can_create_and_read_menu_item(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner3@example.com")
    restaurant = _create_restaurant(client, headers)
    resp = client.post(
        f"/restaurants/{restaurant['id']}/menu-items",
        json={"name": "Margherita", "description": "Classic", "price": "9.99", "category": "Pizza"},
        headers=headers,
    )
    assert resp.status_code == 201
    item = resp.json()
    assert item["name"] == "Margherita"
    assert item["restaurant_id"] == restaurant["id"]

    get_resp = client.get(f"/restaurants/{restaurant['id']}/menu-items/{item['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["price"] == "9.99"


def test_create_menu_item_missing_price_returns_422(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner4@example.com")
    restaurant = _create_restaurant(client, headers)
    resp = client.post(
        f"/restaurants/{restaurant['id']}/menu-items",
        json={"name": "Mystery Dish"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_menu_item_negative_price_returns_422(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner5@example.com")
    restaurant = _create_restaurant(client, headers)
    resp = client.post(
        f"/restaurants/{restaurant['id']}/menu-items",
        json={"name": "Free Soup", "price": "-1.00"},
        headers=headers,
    )
    assert resp.status_code == 422


def test_create_duplicate_menu_item_name_returns_409(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner6@example.com")
    restaurant = _create_restaurant(client, headers)
    payload = {"name": "Pepperoni", "price": "11.50"}
    client.post(f"/restaurants/{restaurant['id']}/menu-items", json=payload, headers=headers)
    resp = client.post(f"/restaurants/{restaurant['id']}/menu-items", json=payload, headers=headers)
    assert resp.status_code == 409


def test_non_owner_cannot_create_menu_item(client: TestClient) -> None:
    owner_headers = register_and_login(client, "menuowner7@example.com")
    restaurant = _create_restaurant(client, owner_headers)

    intruder_headers = register_and_login(client, "menuintruder1@example.com")
    resp = client.post(
        f"/restaurants/{restaurant['id']}/menu-items",
        json={"name": "Hacked Item", "price": "1.00"},
        headers=intruder_headers,
    )
    assert resp.status_code == 403


def test_non_owner_cannot_update_menu_item(client: TestClient) -> None:
    owner_headers = register_and_login(client, "menuowner8@example.com")
    restaurant = _create_restaurant(client, owner_headers)
    item = client.post(
        f"/restaurants/{restaurant['id']}/menu-items",
        json={"name": "Veggie Slice", "price": "7.00"},
        headers=owner_headers,
    ).json()

    intruder_headers = register_and_login(client, "menuintruder2@example.com")
    resp = client.put(
        f"/restaurants/{restaurant['id']}/menu-items/{item['id']}",
        json={"price": "0.01"},
        headers=intruder_headers,
    )
    assert resp.status_code == 403


def test_owner_can_update_menu_item(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner9@example.com")
    restaurant = _create_restaurant(client, headers)
    item = client.post(
        f"/restaurants/{restaurant['id']}/menu-items",
        json={"name": "Calzone", "price": "10.00"},
        headers=headers,
    ).json()

    resp = client.put(
        f"/restaurants/{restaurant['id']}/menu-items/{item['id']}",
        json={"price": "12.00"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["price"] == "12.00"


def test_owner_can_delete_menu_item(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner10@example.com")
    restaurant = _create_restaurant(client, headers)
    item = client.post(
        f"/restaurants/{restaurant['id']}/menu-items",
        json={"name": "Garlic Bread", "price": "4.50"},
        headers=headers,
    ).json()

    resp = client.delete(
        f"/restaurants/{restaurant['id']}/menu-items/{item['id']}", headers=headers
    )
    assert resp.status_code == 204

    get_resp = client.get(f"/restaurants/{restaurant['id']}/menu-items/{item['id']}")
    assert get_resp.status_code == 404


def test_get_nonexistent_menu_item_returns_404(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner11@example.com")
    restaurant = _create_restaurant(client, headers)
    resp = client.get(f"/restaurants/{restaurant['id']}/menu-items/99999")
    assert resp.status_code == 404


def test_menu_items_appear_on_restaurant_detail(client: TestClient) -> None:
    headers = register_and_login(client, "menuowner12@example.com")
    restaurant = _create_restaurant(client, headers)
    client.post(
        f"/restaurants/{restaurant['id']}/menu-items",
        json={"name": "Side Salad", "price": "3.50"},
        headers=headers,
    )
    resp = client.get(f"/restaurants/{restaurant['id']}")
    assert resp.status_code == 200
    menu_items = resp.json()["menu_items"]
    assert len(menu_items) == 1
    assert menu_items[0]["name"] == "Side Salad"
