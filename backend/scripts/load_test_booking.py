#!/usr/bin/env python3
"""Modest parallel load on POST /appointments; prints counts and p95 latency."""

from __future__ import annotations

import asyncio
import statistics
import time
from datetime import datetime, timezone

import httpx
from httpx import ASGITransport

from app.core.database import SessionLocal, init_db
from app.main import app
from app.services.seed import run_seed

PARALLEL = 20


async def main() -> None:
    init_db()
    with SessionLocal() as db:
        seed = run_seed(db)

    resource_id = seed.resource_ids[0]
    customer_id = seed.customer_ids[0]
    start = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 15, 11, 0, tzinfo=timezone.utc)
    payload = {
        "resource_id": resource_id,
        "customer_id": customer_id,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
    }

    transport = ASGITransport(app=app)
    latencies_ms: list[float] = []

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async def one_post():
            t0 = time.perf_counter()
            r = await client.post("/appointments", json=payload)
            latencies_ms.append((time.perf_counter() - t0) * 1000)
            return r.status_code

        codes = await asyncio.gather(*(one_post() for _ in range(PARALLEL)))

    ok = sum(1 for c in codes if c == 201)
    conflict = sum(1 for c in codes if c == 409)
    other = [c for c in codes if c not in (201, 409)]

    latencies_ms.sort()
    p95 = latencies_ms[int(0.95 * len(latencies_ms)) - 1] if latencies_ms else 0.0

    print(f"Parallel POST count: {PARALLEL}")
    print(f"HTTP 201 (created): {ok}")
    print(f"HTTP 409 (conflict): {conflict}")
    if other:
        print(f"Other status codes: {other}")
    print(f"Latency ms — median: {statistics.median(latencies_ms):.2f}, p95: {p95:.2f}")

    with SessionLocal() as db:
        from sqlalchemy import func, select

        from app.models.appointment import CONFIRMED, Appointment

        count = db.scalar(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.resource_id == resource_id,
                Appointment.status == CONFIRMED,
                Appointment.start_utc == start,
            )
        )
        print(f"CONFIRMED rows for this slot in DB: {count}")

    if ok != 1 or conflict != PARALLEL - 1:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
