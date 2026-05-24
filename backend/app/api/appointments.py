from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AvailabilityResponse, BusyBlock
from app.services.booking import BookingService
from app.services.exceptions import NotFoundError, SlotConflictError, ValidationError

router = APIRouter(tags=["appointments"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/appointments", response_model=AppointmentRead, status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)) -> AppointmentRead:
    service = BookingService(db)
    try:
        appt = service.create_booking(
            resource_id=payload.resource_id,
            customer_id=payload.customer_id,
            start_utc=payload.start_utc,
            end_utc=payload.end_utc,
            service_id=payload.service_id,
            client_request_id=payload.client_request_id,
        )
        return AppointmentRead.model_validate(appt)
    except SlotConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/appointments", response_model=list[AppointmentRead])
def list_appointments(
    resource_id: str | None = Query(default=None),
    business_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AppointmentRead]:
    service = BookingService(db)
    rows = service.list_appointments(resource_id=resource_id, business_id=business_id)
    return [AppointmentRead.model_validate(r) for r in rows]


@router.post("/appointments/{appointment_id}/cancel", response_model=AppointmentRead)
def cancel_appointment(appointment_id: str, db: Session = Depends(get_db)) -> AppointmentRead:
    service = BookingService(db)
    try:
        appt = service.cancel_booking(appointment_id)
        return AppointmentRead.model_validate(appt)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/availability", response_model=AvailabilityResponse)
def get_availability(
    resource_id: str,
    range_start_utc: str,
    range_end_utc: str,
    db: Session = Depends(get_db),
) -> AvailabilityResponse:
    from datetime import datetime

    service = BookingService(db)
    try:
        start = datetime.fromisoformat(range_start_utc.replace("Z", "+00:00"))
        end = datetime.fromisoformat(range_end_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid datetime range") from exc

    blocks = service.busy_blocks(resource_id, start, end)
    return AvailabilityResponse(
        resource_id=resource_id,
        range_start_utc=start,
        range_end_utc=end,
        busy=[BusyBlock(start_utc=s, end_utc=e) for s, e in blocks],
    )
