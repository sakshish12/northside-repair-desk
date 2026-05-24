from datetime import datetime, timezone

from app.services.overlap import intervals_overlap


def test_partial_overlap():
    a0 = datetime(2026, 5, 10, 10, 0, tzinfo=timezone.utc)
    a1 = datetime(2026, 5, 10, 11, 0, tzinfo=timezone.utc)
    b0 = datetime(2026, 5, 10, 10, 30, tzinfo=timezone.utc)
    b1 = datetime(2026, 5, 10, 11, 30, tzinfo=timezone.utc)
    assert intervals_overlap(a0, a1, b0, b1) is True


def test_touching_endpoints_do_not_overlap():
    a0 = datetime(2026, 5, 10, 10, 0, tzinfo=timezone.utc)
    a1 = datetime(2026, 5, 10, 11, 0, tzinfo=timezone.utc)
    b0 = datetime(2026, 5, 10, 11, 0, tzinfo=timezone.utc)
    b1 = datetime(2026, 5, 10, 12, 0, tzinfo=timezone.utc)
    assert intervals_overlap(a0, a1, b0, b1) is False


def test_adjacent_before_no_overlap():
    a0 = datetime(2026, 5, 10, 9, 0, tzinfo=timezone.utc)
    a1 = datetime(2026, 5, 10, 10, 0, tzinfo=timezone.utc)
    b0 = datetime(2026, 5, 10, 10, 0, tzinfo=timezone.utc)
    b1 = datetime(2026, 5, 10, 11, 0, tzinfo=timezone.utc)
    assert intervals_overlap(a0, a1, b0, b1) is False
