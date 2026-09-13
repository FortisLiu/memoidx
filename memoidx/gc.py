import json
from pathlib import Path
from datetime import timedelta
from .clock import now_utc, parse_datetime, serialize_datetime
from .locking import root_lock
from .repository import memories
from .retention import expired, settings
from .transactions import _recover, commit_changes
from .format import serialize_memory
from .models import MemoryFile
from .folders import listings


def collect(root, clock=None, dry_run=False, if_due=False):
    with root_lock(root):
        if not dry_run:
            _recover(root)
        now = now_utc(clock)
        config = settings(root)
        last_path = Path(root) / "_state" / "last_gc.json"
        if if_due and last_path.exists():
            last = parse_datetime(json.loads(last_path.read_text())["time"])
            if now < last + timedelta(hours=24):
                return []
        changes, actions = {}, []
        files = dict(memories(root))
        for path, memory in list(files.items()):
            old = [u for u in memory.units if expired(u, now, config["retention_months"])]
            for unit in old:
                record = MemoryFile(memory.id, ("Pending maintenance",) * 3, unit.latest_used_time, "pending", [unit])
                changes[f"_state/trash/{unit.id}.json"] = json.dumps({"path": path, "trashed_at": serialize_datetime(now), "memory": serialize_memory(record)}, ensure_ascii=False)
                actions.append({"id": unit.id, "path": path, "action": "trash", "lut": serialize_datetime(unit.latest_used_time)})
            if old:
                memory.units = [u for u in memory.units if u not in old]
                if memory.units:
                    memory.latest_used_time = max(u.latest_used_time for u in memory.units)
                    memory.summary = ("Pending maintenance",) * 3
                    memory.summary_of = "pending"
                    changes[path] = serialize_memory(memory)
                else:
                    changes[path] = None
                    del files[path]
        for path in (Path(root) / "_state" / "trash").glob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            if parse_datetime(record["trashed_at"]) + timedelta(days=config["trash_days"]) < now:
                changes[path.relative_to(root).as_posix()] = None
                actions.append({"id": path.stem, "action": "purge"})
        if not dry_run:
            if changes:
                changes.update(listings(files))
            for trace in (Path(root) / "_state" / "searches").glob("*.json"):
                stamp = parse_datetime(json.loads(trace.read_text(encoding="utf-8"))["time"])
                if stamp + timedelta(days=config.get("trace_days", 30)) < now:
                    changes[trace.relative_to(root).as_posix()] = None
            changes["_state/last_gc.json"] = json.dumps({"time": serialize_datetime(now)})
            commit_changes(root, changes)
        return actions
