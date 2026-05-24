from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.business import Business
from app.models.customer import Customer
from app.models.resource import Resource
from app.models.service import Service
from app.schemas.catalog import BusinessRead, CustomerRead, ResourceRead, ServiceRead, SeedSummary
from app.services.seed import run_seed

router = APIRouter(tags=["catalog"])


@router.get("/businesses/{business_id}", response_model=BusinessRead)
def get_business(business_id: str, db: Session = Depends(get_db)) -> BusinessRead:
    row = db.get(Business, business_id)
    if not row:
        raise HTTPException(status_code=404, detail="business not found")
    return BusinessRead.model_validate(row)


@router.get("/businesses/{business_id}/resources", response_model=list[ResourceRead])
def list_resources(business_id: str, db: Session = Depends(get_db)) -> list[ResourceRead]:
    rows = db.scalars(select(Resource).where(Resource.business_id == business_id))
    return [ResourceRead.model_validate(r) for r in rows]


@router.get("/businesses/{business_id}/customers", response_model=list[CustomerRead])
def list_customers(business_id: str, db: Session = Depends(get_db)) -> list[CustomerRead]:
    rows = db.scalars(select(Customer).where(Customer.business_id == business_id))
    return [CustomerRead.model_validate(r) for r in rows]


@router.get("/businesses/{business_id}/services", response_model=list[ServiceRead])
def list_services(business_id: str, db: Session = Depends(get_db)) -> list[ServiceRead]:
    rows = db.scalars(select(Service).where(Service.business_id == business_id))
    return [ServiceRead.model_validate(r) for r in rows]


@router.post("/admin/seed", response_model=SeedSummary)
def seed_database(db: Session = Depends(get_db)) -> SeedSummary:
    """Dev-only: populate Northside Repair Desk demo data."""
    return run_seed(db)
