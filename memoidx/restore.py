import json
from pathlib import Path
from .clock import now_utc
from .locking import root_lock
from .repository import memories
from .transactions import _recover, commit_changes
from .format import parse_memory, serialize_memory
from .paths import ensure_inside
from .folders import listings


def restore(root, identifier, clock=None):
    with root_lock(root):
        _recover(root)
        files = dict(memories(root))
        if any(u.id == identifier for m in files.values() for u in m.units):
            raise ValueError("DUPLICATE_ID")
        trash = ensure_inside(root, f"_state/trash/{identifier}.json")
        record = json.loads(trash.read_text(encoding="utf-8"))
        restored = parse_memory(record["memory"])
        unit = restored.units[0]
        if unit.id != identifier:
            raise ValueError("TRASH_ID_MISMATCH")
        old_lut = unit.latest_used_time.isoformat()
        unit.latest_used_time = now_utc(clock)
        path = record["path"]
        ensure_inside(root, path)
        if path in files:
            memory = files[path]
            memory.units.append(unit)
        else:
            memory = restored
            files[path] = memory
        memory.latest_used_time = max(u.latest_used_time for u in memory.units)
        memory.summary = ("Pending maintenance",) * 3
        memory.summary_of = "pending"
        changes = listings(files)
        changes.update({path: serialize_memory(memory), trash.relative_to(root).as_posix(): None})
        commit_changes(root, changes)
        return {"id": identifier, "original_lut": old_lut, "lut": unit.latest_used_time.isoformat()}
