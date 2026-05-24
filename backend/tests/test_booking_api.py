from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models.appointment import CONFIRMED, Appointment


def _slot():
    start = datetime(2026, 6, 1, 14, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 1, 15, 0, tzinfo=timezone.utc)
    return start, end


def test_health(client: TestClient):
    assert client.get("/health").json() == {"status": "ok"}


def test_sequential_conflict(client: TestClient, seed_data: dict):
    resource_id = seed_data["resource_ids"][0]
    customer_id = seed_data["customer_ids"][0]
    start, end = _slot()
    payload = {
        "resource_id": resource_id,
        "customer_id": customer_id,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
    }
    first = client.post("/appointments", json=payload)
    assert first.status_code == 201
    second = client.post("/appointments", json=payload)
    assert second.status_code == 409


def test_cancel_frees_slot(client: TestClient, seed_data: dict):
    resource_id = seed_data["resource_ids"][0]
    customer_id = seed_data["customer_ids"][0]
    start = datetime(2026, 6, 2, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 2, 11, 0, tzinfo=timezone.utc)
    created = client.post(
        "/appointments",
        json={
            "resource_id": resource_id,
            "customer_id": customer_id,
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
        },
    )
    appt_id = created.json()["id"]
    cancel = client.post(f"/appointments/{appt_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "CANCELLED"

    again = client.post(
        "/appointments",
        json={
            "resource_id": resource_id,
            "customer_id": customer_id,
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
        },
    )
    assert again.status_code == 201


def test_idempotency_same_client_request_id(client: TestClient, seed_data: dict):
    resource_id = seed_data["resource_ids"][1]
    customer_id = seed_data["customer_ids"][1]
    start = datetime(2026, 6, 3, 9, 0, tzinfo=timezone.utc)
    end = datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc)
    payload = {
        "resource_id": resource_id,
        "customer_id": customer_id,
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "client_request_id": "idem-test-001",
    }
    r1 = client.post("/appointments", json=payload)
    r2 = client.post("/appointments", json=payload)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]

    with SessionLocal() as db:
        count = db.scalar(
            select(func.count()).select_from(Appointment).where(
                Appointment.client_request_id == "idem-test-001"
            )
        )
        assert count == 1
