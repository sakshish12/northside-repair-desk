from sqlalchemy import delete, inspect, select, text
from sqlalchemy.orm import Session

from app.core.database import engine
from app.models.appointment import Appointment
from app.models.business import Business
from app.models.customer import Customer
from app.models.resource import Resource
from app.models.service import Service
from app.schemas.catalog import SeedSummary

NORTHSIDE_NAME = "Northside Repair Desk"

DEMO_RESOURCES = [
    {
        "name": "Front counter diagnostics bay",
        "kind": "intake",
        "description": "Quick triage, quotes, and device check-in with the customer at the desk.",
    },
    {
        "name": "Electronics workbench — soldering & boards",
        "kind": "repair",
        "description": "Screen assemblies, charging ports, and component-level repairs.",
    },
    {
        "name": "Battery & power station",
        "kind": "repair",
        "description": "Safe battery replacements and power/charging fault isolation.",
    },
]

DEMO_SERVICES = [
    {
        "name": "Screen replacement",
        "description": "Cracked or unresponsive display; includes test and reseal.",
        "duration_minutes": 90,
    },
    {
        "name": "Battery replacement",
        "description": "New cell installed, health check, and safe disposal of the old pack.",
        "duration_minutes": 45,
    },
    {
        "name": "Charging port repair",
        "description": "Loose or corroded port cleaned or replaced; charging verified before handover.",
        "duration_minutes": 60,
    },
    {
        "name": "Water damage assessment",
        "description": "Inspection, dry-out advice, and honest go/no-go on recovery.",
        "duration_minutes": 30,
    },
    {
        "name": "Data backup & transfer",
        "description": "Backup photos and contacts before repair; restore after work is complete.",
        "duration_minutes": 40,
    },
    {
        "name": "Software & setup check",
        "description": "Updates, account sign-in help, and basic performance tune-up after repair.",
        "duration_minutes": 35,
    },
]

DEMO_CUSTOMERS = [
    {"name": "Jordan Ellis", "email": "jordan.ellis@example.com"},
    {"name": "Priya Nair", "email": "priya.nair@example.com"},
    {"name": "Marcus Chen", "email": "marcus.chen@example.com"},
]


def _ensure_description_columns() -> None:
    """Add description columns on existing SQLite DBs without Alembic."""
    if engine.dialect.name != "sqlite":
        return
    insp = inspect(engine)
    for table, col in [("resources", "description"), ("services", "description")]:
        cols = {c["name"] for c in insp.get_columns(table)}
        if col not in cols:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} VARCHAR(500)"))


def _canonical_business(db: Session) -> Business:
    """One Northside tenant; remove duplicate rows from older seeds."""
    rows = list(
        db.scalars(select(Business).where(Business.name == NORTHSIDE_NAME).order_by(Business.id))
    )
    if not rows:
        business = Business(name=NORTHSIDE_NAME, timezone="UTC")
        db.add(business)
        db.flush()
        return business

    keep = rows[0]
    for duplicate in rows[1:]:
        db.execute(delete(Appointment).where(Appointment.business_id == duplicate.id))
        db.execute(delete(Service).where(Service.business_id == duplicate.id))
        db.execute(delete(Resource).where(Resource.business_id == duplicate.id))
        db.execute(delete(Customer).where(Customer.business_id == duplicate.id))
        db.delete(duplicate)
    db.flush()
    return keep


def _sync_by_name(
    db: Session,
    business_id: str,
    model,
    demo_items: list[dict],
    *,
    match_key: str = "name",
) -> list:
    """Upsert demo rows by name and remove stale catalog entries."""
    existing = list(db.scalars(select(model).where(model.business_id == business_id)))
    by_key = {getattr(row, match_key): row for row in existing}
    demo_keys = {item[match_key] for item in demo_items}
    synced: list = []

    for item in demo_items:
        key = item[match_key]
        row = by_key.get(key)
        if row is None:
            row = model(business_id=business_id, **item)  # type: ignore[arg-type]
            db.add(row)
        else:
            for field, value in item.items():
                setattr(row, field, value)
        synced.append(row)

    for row in existing:
        if getattr(row, match_key) not in demo_keys:
            db.delete(row)

    db.flush()
    return synced


def _apply_demo_catalog(db: Session, business_id: str) -> tuple[list[Resource], list[Service], list[Customer]]:
    resources = _sync_by_name(db, business_id, Resource, DEMO_RESOURCES)
    services = _sync_by_name(db, business_id, Service, DEMO_SERVICES)
    customers = _sync_by_name(db, business_id, Customer, DEMO_CUSTOMERS)
    db.commit()
    return resources, services, customers


def run_seed(db: Session) -> SeedSummary:
    _ensure_description_columns()
    business = _canonical_business(db)
    resources, services, customers = _apply_demo_catalog(db, business.id)

    return SeedSummary(
        business_id=business.id,
        business_name=business.name,
        resource_ids=[r.id for r in resources],
        customer_ids=[c.id for c in customers],
        service_ids=[s.id for s in services],
    )
