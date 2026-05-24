from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from app.core.database import engine
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


def _apply_demo_catalog(db: Session, business_id: str) -> tuple[list[Resource], list[Service], list[Customer]]:
    resources = list(db.scalars(select(Resource).where(Resource.business_id == business_id)))
    services = list(db.scalars(select(Service).where(Service.business_id == business_id)))
    customers = list(db.scalars(select(Customer).where(Customer.business_id == business_id)))

    if not resources:
        resources = [
            Resource(business_id=business_id, **item)  # type: ignore[arg-type]
            for item in DEMO_RESOURCES
        ]
        db.add_all(resources)
    else:
        for i, row in enumerate(resources[: len(DEMO_RESOURCES)]):
            data = DEMO_RESOURCES[i]
            row.name = data["name"]
            row.kind = data["kind"]
            row.description = data["description"]
        for item in DEMO_RESOURCES[len(resources) :]:
            resources.append(Resource(business_id=business_id, **item))  # type: ignore[arg-type]
            db.add(resources[-1])

    if not services:
        services = [
            Service(business_id=business_id, **item)  # type: ignore[arg-type]
            for item in DEMO_SERVICES
        ]
        db.add_all(services)
    else:
        for i, row in enumerate(services[: len(DEMO_SERVICES)]):
            data = DEMO_SERVICES[i]
            row.name = data["name"]
            row.description = data["description"]
            row.duration_minutes = data["duration_minutes"]
        for item in DEMO_SERVICES[len(services) :]:
            services.append(Service(business_id=business_id, **item))  # type: ignore[arg-type]
            db.add(services[-1])

    if not customers:
        customers = [Customer(business_id=business_id, **item) for item in DEMO_CUSTOMERS]
        db.add_all(customers)
    else:
        for i, row in enumerate(customers[: len(DEMO_CUSTOMERS)]):
            data = DEMO_CUSTOMERS[i]
            row.name = data["name"]
            row.email = data["email"]
        for item in DEMO_CUSTOMERS[len(customers) :]:
            customers.append(Customer(business_id=business_id, **item))
            db.add(customers[-1])

    db.commit()
    return resources, services, customers


def run_seed(db: Session) -> SeedSummary:
    _ensure_description_columns()

    existing = db.scalar(select(Business).where(Business.name == NORTHSIDE_NAME))
    if existing:
        resources, services, customers = _apply_demo_catalog(db, existing.id)
        return SeedSummary(
            business_id=existing.id,
            business_name=existing.name,
            resource_ids=[r.id for r in resources],
            customer_ids=[c.id for c in customers],
            service_ids=[s.id for s in services],
        )

    business = Business(name=NORTHSIDE_NAME, timezone="UTC")
    db.add(business)
    db.flush()

    resources, services, customers = _apply_demo_catalog(db, business.id)

    return SeedSummary(
        business_id=business.id,
        business_name=business.name,
        resource_ids=[r.id for r in resources],
        customer_ids=[c.id for c in customers],
        service_ids=[s.id for s in services],
    )
