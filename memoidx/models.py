from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryUnit:
    id: str
    latest_used_time: datetime
    retention: str
    source: str
    content: str


@dataclass
class MemoryFile:
    id: str
    summary: tuple[str, str, str]
    latest_used_time: datetime
    summary_of: str
    units: list[MemoryUnit]
