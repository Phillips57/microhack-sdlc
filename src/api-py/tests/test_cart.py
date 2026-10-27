from __future__ import annotations

import uuid
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    database_file = tmp_path / "cart-test.db"
    monkeypatch.setenv("DB_FILE", str(database_file))
    with TestClient(app) as test_client:
        yield test_client


def test_cart_add_update_remove_and_total(client: TestClient) -> None:
    cart_id = uuid.uuid4()

    empty_cart = client.get(f"/api/cart/{cart_id}").json()
    assert empty_cart == {
        "cartId": str(cart_id),
        "items": [],
        "itemCount": 0,
        "total": 0.0,
    }

    added_cart = client.post(
        f"/api/cart/{cart_id}/items",
        json={"productId": 1, "quantity": 2},
    )
    assert added_cart.status_code == 200
    assert added_cart.json()["items"][0]["unitPrice"] == 97.49
    assert added_cart.json()["items"][0]["lineTotal"] == 194.98
    assert added_cart.json()["total"] == 194.98

    added_again = client.post(
        f"/api/cart/{cart_id}/items",
        json={"productId": 1, "quantity": 1},
    )
    assert added_again.json()["items"][0]["quantity"] == 3
    assert added_again.json()["itemCount"] == 3

    second_product = client.post(
        f"/api/cart/{cart_id}/items",
        json={"productId": 3, "quantity": 1},
    )
    assert second_product.json()["itemCount"] == 4
    assert second_product.json()["total"] == 382.46

    updated_cart = client.put(
        f"/api/cart/{cart_id}/items/1",
        json={"quantity": 4},
    )
    assert updated_cart.json()["items"][0]["quantity"] == 4
    assert updated_cart.json()["total"] == 479.95

    persisted_cart = client.get(f"/api/cart/{cart_id}").json()
    assert persisted_cart == updated_cart.json()

    removed_product = client.delete(f"/api/cart/{cart_id}/items/3")
    assert removed_product.status_code == 204
    assert client.get(f"/api/cart/{cart_id}").json()["total"] == 389.96

    removed = client.delete(f"/api/cart/{cart_id}/items/1")
    assert removed.status_code == 204
    assert client.get(f"/api/cart/{cart_id}").json()["items"] == []


def test_cart_rejects_invalid_products_and_quantities(client: TestClient) -> None:
    cart_id = uuid.uuid4()

    missing_product = client.post(
        f"/api/cart/{cart_id}/items",
        json={"productId": 9999, "quantity": 1},
    )
    assert missing_product.status_code == 404
    assert missing_product.json()["error"]["code"] == "NOT_FOUND"

    invalid_quantity = client.post(
        f"/api/cart/{cart_id}/items",
        json={"productId": 1, "quantity": 0},
    )
    assert invalid_quantity.status_code == 422

    invalid_cart_id = client.get("/api/cart/not-a-uuid")
    assert invalid_cart_id.status_code == 422


def test_cart_rejects_updates_and_removals_for_missing_items(client: TestClient) -> None:
    cart_id = uuid.uuid4()

    update_response = client.put(
        f"/api/cart/{cart_id}/items/1",
        json={"quantity": 2},
    )
    assert update_response.status_code == 404
    assert update_response.json()["error"]["code"] == "NOT_FOUND"

    remove_response = client.delete(f"/api/cart/{cart_id}/items/1")
    assert remove_response.status_code == 404
    assert remove_response.json()["error"]["code"] == "NOT_FOUND"
