from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from database.sqlite import get_connection


def test_wal_can_be_disabled_for_network_database_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DB_FILE", str(tmp_path / "app.db"))
    monkeypatch.setenv("DB_ENABLE_WAL", "false")

    async def journal_mode() -> str:
        async with get_connection() as connection:
            cursor = await connection.execute("PRAGMA journal_mode;")
            row = await cursor.fetchone()
            assert row is not None
            return str(row[0]).lower()

    assert asyncio.run(journal_mode()) == "delete"
