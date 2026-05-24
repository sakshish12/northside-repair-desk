from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.appointment import CONFIRMED, Appointment


def test_cancelled_appointment_does_not_block_slot(client: TestClient, seed_data: dict):
    resource_id = seed_data["resource_ids"][0]
    customer_id = seed_data["customer_ids"][0]
    start = datetime(2026, 6, 10, 14, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 10, 15, 0, tzinfo=timezone.utc)
    body = {
        "resource_id": resource_id,
        "customer_id": customer_id,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
    }
    first = client.post("/appointments", json=body)
    appt_id = first.json()["id"]
    client.post(f"/appointments/{appt_id}/cancel")

    second = client.post("/appointments", json=body)
    assert second.status_code == 201


def test_invalid_interval_rejected(client: TestClient, seed_data: dict):
    resource_id = seed_data["resource_ids"][0]
    customer_id = seed_data["customer_ids"][0]
    start = datetime(2026, 6, 11, 16, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 11, 15, 0, tzinfo=timezone.utc)
    r = client.post(
        "/appointments",
        json={
            "resource_id": resource_id,
            "customer_id": customer_id,
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
        },
    )
    assert r.status_code == 400


def test_utc_offset_accepted_in_api(client: TestClient, seed_data: dict):
    """Explicit UTC offsets in JSON are accepted; API returns ISO timestamps."""
    resource_id = seed_data["resource_ids"][1]
    customer_id = seed_data["customer_ids"][1]
    r = client.post(
        "/appointments",
        json={
            "resource_id": resource_id,
            "customer_id": customer_id,
            "start_utc": "2026-06-12T10:00:00+00:00",
            "end_utc": "2026-06-12T11:00:00+00:00",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert "2026-06-12" in body["start_utc"]
    with SessionLocal() as db:
        row = db.get(Appointment, body["id"])
        assert row is not None
        assert row.start_utc.hour == 10


def test_db_state_after_conflict(client: TestClient, seed_data: dict):
    """After 409, no extra CONFIRMED row is left for the contested slot."""
    resource_id = seed_data["resource_ids"][0]
    customer_id = seed_data["customer_ids"][0]
    start = datetime(2026, 6, 20, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 20, 10, 0, tzinfo=timezone.utc)
    body = {
        "resource_id": resource_id,
        "customer_id": customer_id,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
    }
    client.post("/appointments", json=body)
    conflict = client.post("/appointments", json=body)
    assert conflict.status_code == 409

    with SessionLocal() as db:
        rows = list(
            db.scalars(
                select(Appointment).where(
                    Appointment.resource_id == resource_id,
                    Appointment.status == CONFIRMED,
                    Appointment.start_utc == start,
                )
            )
        )
        assert len(rows) == 1
