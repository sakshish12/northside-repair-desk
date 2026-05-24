from datetime import datetime

from pydantic import BaseModel, Field


class AppointmentCreate(BaseModel):
    resource_id: str
    customer_id: str
    start_utc: datetime
    end_utc: datetime
    service_id: str | None = None
    client_request_id: str | None = Field(default=None, max_length=64)


class AppointmentRead(BaseModel):
    id: str
    business_id: str
    resource_id: str
    customer_id: str
    service_id: str | None
    start_utc: datetime
    end_utc: datetime
    status: str
    client_request_id: str | None

    model_config = {"from_attributes": True}


class BusyBlock(BaseModel):
    start_utc: datetime
    end_utc: datetime


class AvailabilityResponse(BaseModel):
    resource_id: str
    range_start_utc: datetime
    range_end_utc: datetime
    busy: list[BusyBlock]
