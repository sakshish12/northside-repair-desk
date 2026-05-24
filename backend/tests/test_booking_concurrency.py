import asyncio
from datetime import datetime, timezone

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.main import app
from app.models.appointment import CONFIRMED, Appointment


@pytest.mark.asyncio
async def test_parallel_bookings_single_winner(seed_data: dict):
    """Ten concurrent POSTs for the same slot: exactly one 201, nine 409, one CONFIRMED row."""
    resource_id = seed_data["resource_ids"][0]
    customer_id = seed_data["customer_ids"][0]
    start = datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc)
    end = datetime(2026, 7, 1, 13, 0, tzinfo=timezone.utc)
    payload = {
        "resource_id": resource_id,
        "customer_id": customer_id,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
    }

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        async def attempt():
            return await http.post("/appointments", json=payload)

        results = await asyncio.gather(*(attempt() for _ in range(10)))

    ok = [r for r in results if r.status_code == 201]
    conflict = [r for r in results if r.status_code == 409]
    assert len(ok) == 1, f"expected 1 success, got {len(ok)}: {[r.status_code for r in results]}"
    assert len(conflict) == 9

    with SessionLocal() as db:
        count = db.scalar(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.resource_id == resource_id,
                Appointment.status == CONFIRMED,
                Appointment.start_utc == start,
            )
        )
        assert count == 1
