"""Clock helpers used by MemoIdx.

The clock is injectable so tests can be deterministic without changing the
machine's system time.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Callable


UTC_PLUS_8 = timezone(timedelta(hours=8))
Clock = Callable[[], datetime]


def now_utc(clock: Clock | None = None) -> datetime:
    """Return the current time as an aware datetime in UTC+8.

    ``clock`` is injectable for deterministic tests.  Naive values are
    rejected because timestamps must always carry timezone information.
    """
    value = clock() if clock is not None else datetime.now(UTC_PLUS_8)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("clock must return a timezone-aware datetime")
    return value.astimezone(UTC_PLUS_8)


def serialize_datetime(value: datetime) -> str:
    """Serialize an aware datetime in the project's ISO-8601 format."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC_PLUS_8).isoformat(timespec="auto")


def parse_datetime(value: str) -> datetime:
    """Parse a serialized project timestamp."""
    return datetime.fromisoformat(value)
