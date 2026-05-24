from __future__ import annotations

from datetime import datetime


def intervals_overlap(
    a_start: datetime,
    a_end: datetime,
    b_start: datetime,
    b_end: datetime,
) -> bool:
    """Half-open [start, end): touching endpoints do not overlap."""
    return a_start < b_end and b_start < a_end
