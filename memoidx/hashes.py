from __future__ import annotations

import hashlib
import json

from .models import MemoryFile, MemoryUnit


def _digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def unit_revision(unit: MemoryUnit) -> str:
    return _digest({"content": unit.content, "retention": unit.retention, "source": unit.source})


def file_summary_source_hash(memory: MemoryFile) -> str:
    return _digest([{"id": unit.id, "content": unit.content} for unit in memory.units])
