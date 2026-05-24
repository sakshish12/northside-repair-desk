import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

CONFIRMED = "CONFIRMED"
CANCELLED = "CANCELLED"


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("client_request_id", name="uq_appointments_client_request_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id"), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(36), ForeignKey("resources.id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    service_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("services.id"), nullable=True)
    start_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=CONFIRMED)
    client_request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)

    resource: Mapped["Resource"] = relationship(back_populates="appointments")
    customer: Mapped["Customer"] = relationship(back_populates="appointments")
