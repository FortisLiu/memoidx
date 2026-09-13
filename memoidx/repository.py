"""Read helpers. Callers hold the root lock for a consistent snapshot."""
from pathlib import Path
from .format import parse_memory
from .transactions import require_recovered
from .paths import ensure_inside
from .hashes import unit_revision
from .clock import serialize_datetime


def memories(root):
    root = Path(root)
    require_recovered(root)
    seen = set()
    result = []
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if "_state" in relative.parts or path.name == "README.md":
            continue
        ensure_inside(root, relative)
        memory = parse_memory(path.read_text(encoding="utf-8"), str(path))
        for identifier in [memory.id, *(u.id for u in memory.units)]:
            if identifier in seen:
                raise ValueError("DUPLICATE_ID: " + identifier)
            seen.add(identifier)
        result.append((relative.as_posix(), memory))
    return result


def locate(root, identifier):
    for path, memory in memories(root):
        for unit in memory.units:
            if unit.id == identifier:
                return path, memory, unit
    raise ValueError("UNIT_NOT_FOUND: " + identifier)


def describe(path, unit):
    return dict(id=unit.id, path=path, content=unit.content, source=unit.source,
                retention=unit.retention, lut=serialize_datetime(unit.latest_used_time),
                revision=unit_revision(unit))
