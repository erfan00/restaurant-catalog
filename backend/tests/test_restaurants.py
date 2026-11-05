"""CRUD tests for /restaurants."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import register_and_login


def test_list_restaurants_empty(client: TestClient) -> None:
    resp = client.get("/restaurants")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_restaurant_requires_auth(client: TestClient) -> None:
    resp = client.post("/restaurants", json={"name": "Pasta Place"})
    assert resp.status_code == 401


def test_create_and_get_restaurant(client: TestClient) -> None:
    headers = register_and_login(client, "owner1@example.com")
    resp = client.post(
        "/restaurants",
        json={"name": "Pasta Place", "cuisine": "Italian", "description": "Cozy spot"},
        headers=headers,
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == "Pasta Place"
    assert created["owner_id"]

    get_resp = client.get(f"/restaurants/{created['id']}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["name"] == "Pasta Place"
    assert body["menu_items"] == []


def test_create_restaurant_missing_name_returns_422(client: TestClient) -> None:
    headers = register_and_login(client, "owner2@example.com")
    resp = client.post("/restaurants", json={"cuisine": "Mexican"}, headers=headers)
    assert resp.status_code == 422


def test_create_restaurant_duplicate_name_returns_409(client: TestClient) -> None:
    headers = register_and_login(client, "owner3@example.com")
    client.post("/restaurants", json={"name": "Taco Town"}, headers=headers)
    resp = client.post("/restaurants", json={"name": "Taco Town"}, headers=headers)
    assert resp.status_code == 409


def test_get_nonexistent_restaurant_returns_404(client: TestClient) -> None:
    resp = client.get("/restaurants/9999")
    assert resp.status_code == 404


def test_list_restaurants_after_create(client: TestClient) -> None:
    headers = register_and_login(client, "owner4@example.com")
    client.post("/restaurants", json={"name": "Sushi Spot"}, headers=headers)
    resp = client.get("/restaurants")
    assert resp.status_code == 200
    names = [r["name"] for r in resp.json()]
    assert "Sushi Spot" in names


def test_owner_can_update_own_restaurant(client: TestClient) -> None:
    headers = register_and_login(client, "owner5@example.com")
    created = client.post("/restaurants", json={"name": "Burger Barn"}, headers=headers).json()
    resp = client.put(
        f"/restaurants/{created['id']}",
        json={"description": "Now with fries"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Now with fries"


def test_update_restaurant_requires_auth(client: TestClient) -> None:
    headers = register_and_login(client, "owner6@example.com")
    created = client.post("/restaurants", json={"name": "Noodle Nook"}, headers=headers).json()
    resp = client.put(f"/restaurants/{created['id']}", json={"description": "x"})
    assert resp.status_code == 401


def test_non_owner_cannot_update_restaurant(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner7@example.com")
    created = client.post(
        "/restaurants", json={"name": "Dumpling Den"}, headers=owner_headers
    ).json()

    other_headers = register_and_login(client, "intruder1@example.com")
    resp = client.put(
        f"/restaurants/{created['id']}", json={"description": "hacked"}, headers=other_headers
    )
    assert resp.status_code == 403


def test_non_owner_cannot_delete_restaurant(client: TestClient) -> None:
    owner_headers = register_and_login(client, "owner8@example.com")
    created = client.post(
        "/restaurants", json={"name": "Waffle World"}, headers=owner_headers
    ).json()

    other_headers = register_and_login(client, "intruder2@example.com")
    resp = client.delete(f"/restaurants/{created['id']}", headers=other_headers)
    assert resp.status_code == 403

    # still there afterwards
    get_resp = client.get(f"/restaurants/{created['id']}")
    assert get_resp.status_code == 200


def test_owner_can_delete_own_restaurant(client: TestClient) -> None:
    headers = register_and_login(client, "owner9@example.com")
    created = client.post("/restaurants", json={"name": "Pie Palace"}, headers=headers).json()
    resp = client.delete(f"/restaurants/{created['id']}", headers=headers)
    assert resp.status_code == 204

    get_resp = client.get(f"/restaurants/{created['id']}")
    assert get_resp.status_code == 404


def test_update_nonexistent_restaurant_returns_404(client: TestClient) -> None:
    headers = register_and_login(client, "owner10@example.com")
    resp = client.put("/restaurants/12345", json={"description": "x"}, headers=headers)
    assert resp.status_code == 404


def test_delete_nonexistent_restaurant_returns_404(client: TestClient) -> None:
    headers = register_and_login(client, "owner11@example.com")
    resp = client.delete("/restaurants/12345", headers=headers)
    assert resp.status_code == 404
