"""
Timestamps only -- this app has no calendar-day business logic, just an
audit trail of when each photo was captured, so it's a straight UTC 'now'
in a fixed, sortable string format (no timezone-of-record subtleties).
"""
from __future__ import annotations

from datetime import datetime, timezone

_UTC = timezone.utc


def now_db() -> str:
    """Current instant as 'YYYY-MM-DDTHH:MM:SS.mmm+00:00', for createdAt columns."""
    dt = datetime.now(_UTC)
    ms = f"{dt.microsecond // 1000:03d}"
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{ms}+00:00")
