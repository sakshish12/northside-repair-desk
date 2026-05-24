from pydantic import BaseModel


class ResourceRead(BaseModel):
    id: str
    business_id: str
    name: str
    kind: str
    description: str | None = None

    model_config = {"from_attributes": True}


class CustomerRead(BaseModel):
    id: str
    business_id: str
    name: str
    email: str | None

    model_config = {"from_attributes": True}


class ServiceRead(BaseModel):
    id: str
    business_id: str
    name: str
    description: str | None = None
    duration_minutes: int

    model_config = {"from_attributes": True}


class BusinessRead(BaseModel):
    id: str
    name: str
    timezone: str

    model_config = {"from_attributes": True}


class SeedSummary(BaseModel):
    business_id: str
    business_name: str
    resource_ids: list[str]
    customer_ids: list[str]
    service_ids: list[str]
