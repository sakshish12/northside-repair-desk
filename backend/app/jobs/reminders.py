"""Reminder job: selects due appointments and logs mock notifications."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.models.appointment import CONFIRMED, Appointment

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("northside.reminders")


def run_reminder_job(lookahead_hours: int = 24) -> int:
    init_db()
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=lookahead_hours)
    sent = 0

    with SessionLocal() as db:
        due = db.scalars(
            select(Appointment).where(
                Appointment.status == CONFIRMED,
                Appointment.start_utc >= now,
                Appointment.start_utc <= window_end,
            )
        )
        for appt in due:
            msg = (
                f"[{settings.mail_mode}] reminder appointment={appt.id} "
                f"resource={appt.resource_id} starts={appt.start_utc.isoformat()}"
            )
            logger.info(msg)
            sent += 1

    return sent


if __name__ == "__main__":
    count = run_reminder_job()
    logger.info("reminders processed: %s", count)
    sys.exit(0)
