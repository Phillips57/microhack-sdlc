from __future__ import annotations

from contextlib import asynccontextmanager

import aiosqlite
from fastapi.testclient import TestClient
import pytest

import main


class UnavailableConnection:
    async def execute(self, _: str) -> None:
        raise aiosqlite.OperationalError("database unavailable")


def test_root() -> None:
    with TestClient(main.app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "Hello, world!"


def test_liveness() -> None:
    with TestClient(main.app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_checks_database() -> None:
    with TestClient(main.app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_reports_database_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    @asynccontextmanager
    async def unavailable_connection():
        yield UnavailableConnection()

    monkeypatch.setattr(main, "get_connection", unavailable_connection)
    with TestClient(main.app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "dependency": "database"}
