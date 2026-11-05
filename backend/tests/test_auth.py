"""Tests for registration/login (OAuth2 password + JWT flow)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import register_and_login


def test_register_user(client: TestClient) -> None:
    resp = client.post(
        "/auth/register", json={"email": "alice@example.com", "password": "password123"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body
    assert "hashed_password" not in body  # never leak the hash


def test_register_duplicate_email_rejected(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "bob@example.com", "password": "password123"})
    resp = client.post(
        "/auth/register", json={"email": "bob@example.com", "password": "other12345"}
    )
    assert resp.status_code == 409


def test_register_missing_fields_returns_422(client: TestClient) -> None:
    resp = client.post("/auth/register", json={"email": "no-password@example.com"})
    assert resp.status_code == 422


def test_register_short_password_returns_422(client: TestClient) -> None:
    resp = client.post("/auth/register", json={"email": "short@example.com", "password": "short"})
    assert resp.status_code == 422


def test_register_invalid_email_returns_422(client: TestClient) -> None:
    resp = client.post("/auth/register", json={"email": "not-an-email", "password": "password123"})
    assert resp.status_code == 422


def test_login_success_returns_jwt(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "carol@example.com", "password": "password123"})
    resp = client.post(
        "/auth/token", data={"username": "carol@example.com", "password": "password123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 10


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "dave@example.com", "password": "password123"})
    resp = client.post("/auth/token", data={"username": "dave@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user_returns_401(client: TestClient) -> None:
    resp = client.post(
        "/auth/token", data={"username": "ghost@example.com", "password": "whatever123"}
    )
    assert resp.status_code == 401


def test_me_endpoint_requires_auth(client: TestClient) -> None:
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_me_endpoint_returns_current_user(client: TestClient) -> None:
    headers = register_and_login(client, "erin@example.com")
    resp = client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "erin@example.com"


def test_me_endpoint_rejects_garbage_token(client: TestClient) -> None:
    resp = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_google_login_disabled_by_default(client: TestClient) -> None:
    resp = client.get("/auth/google/login")
    assert resp.status_code == 501
