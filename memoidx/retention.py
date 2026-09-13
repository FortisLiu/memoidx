import calendar
import json
from pathlib import Path
from .clock import now_utc


def settings(root):
    path = Path(root) / "config.json"
    config = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return {"retention_months": 6, "trash_days": 30, **config}


def cutoff(now, months=6):
    if not isinstance(months, int) or months < 0:
        raise ValueError("INVALID_RETENTION_MONTHS")
    index = now.year * 12 + now.month - 1 - months
    year, month = divmod(index, 12)
    month += 1
    return now.replace(year=year, month=month, day=min(now.day, calendar.monthrange(year, month)[1]))


def expired(unit, now, months=6):
    if unit.latest_used_time > now:
        raise ValueError("FUTURE_TIMESTAMP: " + unit.id)
    return unit.retention == "normal" and unit.latest_used_time < cutoff(now, months)
