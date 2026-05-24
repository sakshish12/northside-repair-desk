from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.appointment import CONFIRMED, CANCELLED, Appointment
from app.models.customer import Customer
from app.models.resource import Resource
from app.services.exceptions import NotFoundError, SlotConflictError, ValidationError
from app.services.overlap import intervals_overlap


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class BookingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _begin_immediate(self) -> None:
        """SQLite: acquire write lock early to reduce check-then-act races."""
        bind = self.db.get_bind()
        if bind.dialect.name == "sqlite":
            self.db.execute(text("BEGIN IMMEDIATE"))

    def _has_overlap(
        self,
        resource_id: str,
        start_utc: datetime,
        end_utc: datetime,
        exclude_appointment_id: str | None = None,
    ) -> bool:
        start_utc = _ensure_utc(start_utc)
        end_utc = _ensure_utc(end_utc)
        if start_utc >= end_utc:
            raise ValidationError("start must be before end")

        stmt = select(Appointment).where(
            Appointment.resource_id == resource_id,
            Appointment.status == CONFIRMED,
        )
        if exclude_appointment_id:
            stmt = stmt.where(Appointment.id != exclude_appointment_id)

        for existing in self.db.scalars(stmt):
            if intervals_overlap(
                start_utc, end_utc, _ensure_utc(existing.start_utc), _ensure_utc(existing.end_utc)
            ):
                return True
        return False

    def create_booking(
        self,
        *,
        resource_id: str,
        customer_id: str,
        start_utc: datetime,
        end_utc: datetime,
        service_id: str | None = None,
        client_request_id: str | None = None,
    ) -> Appointment:
        resource = self.db.get(Resource, resource_id)
        if not resource:
            raise NotFoundError("resource not found")
        customer = self.db.get(Customer, customer_id)
        if not customer:
            raise NotFoundError("customer not found")
        if customer.business_id != resource.business_id:
            raise ValidationError("customer does not belong to resource business")

        if client_request_id:
            existing = self.db.scalar(
                select(Appointment).where(Appointment.client_request_id == client_request_id)
            )
            if existing:
                return existing

        self._begin_immediate()
        if self._has_overlap(resource_id, start_utc, end_utc):
            if client_request_id:
                existing = self.db.scalar(
                    select(Appointment).where(Appointment.client_request_id == client_request_id)
                )
                if existing:
                    self.db.rollback()
                    return existing
            self.db.rollback()
            raise SlotConflictError("slot no longer available")

        appointment = Appointment(
            business_id=resource.business_id,
            resource_id=resource_id,
            customer_id=customer_id,
            service_id=service_id,
            start_utc=_ensure_utc(start_utc),
            end_utc=_ensure_utc(end_utc),
            status=CONFIRMED,
            client_request_id=client_request_id,
        )
        self.db.add(appointment)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if client_request_id:
                existing = self.db.scalar(
                    select(Appointment).where(Appointment.client_request_id == client_request_id)
                )
                if existing:
                    return existing
            raise SlotConflictError("slot no longer available") from None
        self.db.refresh(appointment)
        return appointment

    def cancel_booking(self, appointment_id: str) -> Appointment:
        self._begin_immediate()
        appointment = self.db.get(Appointment, appointment_id)
        if not appointment:
            self.db.rollback()
            raise NotFoundError("appointment not found")
        if appointment.status == CANCELLED:
            self.db.rollback()
            raise ValidationError("appointment already cancelled")

        appointment.status = CANCELLED
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def list_appointments(
        self,
        *,
        resource_id: str | None = None,
        business_id: str | None = None,
    ) -> list[Appointment]:
        stmt = select(Appointment).order_by(Appointment.start_utc)
        if resource_id:
            stmt = stmt.where(Appointment.resource_id == resource_id)
        if business_id:
            stmt = stmt.where(Appointment.business_id == business_id)
        return list(self.db.scalars(stmt))

    def busy_blocks(
        self,
        resource_id: str,
        range_start: datetime,
        range_end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        range_start = _ensure_utc(range_start)
        range_end = _ensure_utc(range_end)
        blocks: list[tuple[datetime, datetime]] = []
        for appt in self.db.scalars(
            select(Appointment).where(
                Appointment.resource_id == resource_id,
                Appointment.status == CONFIRMED,
            )
        ):
            s, e = _ensure_utc(appt.start_utc), _ensure_utc(appt.end_utc)
            if intervals_overlap(range_start, range_end, s, e):
                blocks.append((s, e))
        return sorted(blocks, key=lambda x: x[0])
