"""Focused tests proving server-side ownership/authorization enforcement.

These complement the CRUD tests in test_restaurants.py / test_menu_items.py
with explicit coverage of the 401-vs-403 distinction and token edge cases
called out in the project requirements.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from tests.conftest import register_and_login


def test_no_token_is_401_not_403(client: TestClient) -> None:
    headers = register_and_login(client, "auth-owner1@example.com")
    restaurant = client.post("/restaurants", json={"name": "Ramen Room"}, headers=headers).json()

    resp = client.delete(f"/restaurants/{restaurant['id']}")
    assert resp.status_code == 401


def test_wrong_owner_is_403_not_401(client: TestClient) -> None:
    owner_headers = register_and_login(client, "auth-owner2@example.com")
    restaurant = client.post(
        "/restaurants", json={"name": "Curry Corner"}, headers=owner_headers
    ).json()

    other_headers = register_and_login(client, "auth-intruder1@example.com")
    resp = client.delete(f"/restaurants/{restaurant['id']}", headers=other_headers)
    assert resp.status_code == 403


def test_expired_or_malformed_token_rejected(client: TestClient) -> None:
    resp = client.get("/auth/me", headers={"Authorization": "Bearer totally.not.a.jwt"})
    assert resp.status_code == 401


def test_token_for_deleted_user_rejected(client: TestClient) -> None:
    # Forge a token for a user id that doesn't exist in this fresh DB.
    token = create_access_token(subject="999999")
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_malformed_authorization_header_is_treated_as_unauthenticated(client: TestClient) -> None:
    resp = client.get("/auth/me", headers={"Authorization": "NotBearer sometoken"})
    assert resp.status_code == 401


def test_public_endpoints_do_not_require_auth(client: TestClient) -> None:
    headers = register_and_login(client, "auth-owner3@example.com")
    restaurant = client.post("/restaurants", json={"name": "Open Kitchen"}, headers=headers).json()

    assert client.get("/restaurants").status_code == 200
    assert client.get(f"/restaurants/{restaurant['id']}").status_code == 200
    assert client.get(f"/restaurants/{restaurant['id']}/menu-items").status_code == 200
