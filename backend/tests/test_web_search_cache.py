import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, OperationalError


def _pg_reachable() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    if not url.startswith("postgresql"):
        return False
    try:
        eng = create_engine(url, pool_pre_ping=True)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
        return True
    except (OperationalError, DBAPIError, OSError):
        return False


pytestmark = pytest.mark.skipif(
    not _pg_reachable(),
    reason="PostgreSQL not listening (e.g. docker compose up -d postgres)",
)

from src.main import app  # noqa: E402


def test_lookup_miss_then_store_hit() -> None:
    with TestClient(app) as client:
        _run_cache_roundtrip(client)


def _run_cache_roundtrip(client: TestClient) -> None:
    r0 = client.post(
        "/api/web-search-cache/lookup",
        json={"query": "acme widgets"},
    )
    assert r0.status_code == 200
    assert r0.json() == {"found": False, "result": None}

    sample = '{"organic": []}'
    r1 = client.post(
        "/api/web-search-cache",
        json={"query": "acme widgets", "result": sample},
    )
    assert r1.status_code == 204

    r2 = client.post(
        "/api/web-search-cache/lookup",
        json={"query": "acme widgets"},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["found"] is True
    assert data["result"] == sample
