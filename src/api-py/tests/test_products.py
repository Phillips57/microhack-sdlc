from __future__ import annotations

from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    database_file = tmp_path / "products-test.db"
    monkeypatch.setenv("DB_FILE", str(database_file))
    with TestClient(app) as test_client:
        yield test_client


def test_get_all_products_without_filters(client: TestClient) -> None:
    response = client.get("/api/products")

    assert response.status_code == 200
    products = response.json()
    assert len(products) == 12
    assert [product["productId"] for product in products] == list(range(1, 13))


@pytest.mark.parametrize(
    ("query", "expected_product_id"),
    [("smartfeeder", 1), ("cat-flix-001", 3)],
)
def test_search_products_by_name_or_sku_case_insensitively(
    client: TestClient,
    query: str,
    expected_product_id: int,
) -> None:
    response = client.get("/api/products", params={"q": query})

    assert response.status_code == 200
    assert [product["productId"] for product in response.json()] == [expected_product_id]


def test_search_and_inclusive_price_bounds(client: TestClient) -> None:
    response = client.get(
        "/api/products",
        params={"q": "CAT-FLIX", "min_price": 89.99, "max_price": 89.99},
    )

    assert response.status_code == 200
    assert [product["productId"] for product in response.json()] == [3]


def test_price_bounds_match_discounted_price_displayed_to_customers(client: TestClient) -> None:
    response = client.get(
        "/api/products",
        params={"q": "smartfeeder", "min_price": 97.49, "max_price": 97.49},
    )

    assert response.status_code == 200
    assert [product["productId"] for product in response.json()] == [1]


def test_search_without_matches_returns_empty_list(client: TestClient) -> None:
    response = client.get("/api/products", params={"q": "space tuna"})

    assert response.status_code == 200
    assert response.json() == []


def test_reversed_price_bounds_return_validation_error(client: TestClient) -> None:
    response = client.get(
        "/api/products",
        params={"min_price": 100, "max_price": 50},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "min_price must be less than or equal to max_price" in response.json()["error"]["message"]
