import asyncio
from datetime import datetime, timezone

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.main import app
from app.models.appointment import Appointment


@pytest.mark.asyncio
async def test_parallel_same_client_request_id_one_row(seed_data: dict):
    """Duplicate submits with the same idempotency key must not create multiple rows."""
    resource_id = seed_data["resource_ids"][0]
    customer_id = seed_data["customer_ids"][0]
    start = datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 7, 2, 10, 0, tzinfo=timezone.utc)
    payload = {
        "resource_id": resource_id,
        "customer_id": customer_id,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "client_request_id": "parallel-idem-key-001",
    }

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        results = await asyncio.gather(*(http.post("/appointments", json=payload) for _ in range(10)))

    assert all(r.status_code == 201 for r in results)
    ids = {r.json()["id"] for r in results}
    assert len(ids) == 1

    with SessionLocal() as db:
        count = db.scalar(
            select(func.count()).select_from(Appointment).where(
                Appointment.client_request_id == "parallel-idem-key-001"
            )
        )
        assert count == 1
