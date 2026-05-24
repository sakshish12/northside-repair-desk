import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Must set before app import
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_northside.db")

from app.core.database import SessionLocal, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.seed import run_seed  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _init_database() -> Generator[None, None, None]:
    test_db = Path("test_northside.db")
    if test_db.exists():
        test_db.unlink()
    init_db()
    with SessionLocal() as db:
        run_seed(db)
    yield
    engine.dispose()
    if test_db.exists():
        test_db.unlink()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seed_data(client: TestClient) -> dict:
    data = client.post("/admin/seed").json()
    return data
