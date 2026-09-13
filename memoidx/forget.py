from pathlib import Path
from .locking import root_lock
from .repository import memories
from .transactions import _recover, commit_changes
from .format import serialize_memory
from .paths import ensure_inside
from .folders import listings
import json


def forget(root, identifier):
    with root_lock(root):
        _recover(root)
        files = dict(memories(root))
        changes = {}
        for path, memory in list(files.items()):
            remaining = [u for u in memory.units if u.id != identifier]
            if len(remaining) != len(memory.units):
                memory.units = remaining
                if remaining:
                    memory.latest_used_time = max(u.latest_used_time for u in remaining)
                    memory.summary = ("Pending maintenance",) * 3
                    memory.summary_of = "pending"
                    changes[path] = serialize_memory(memory)
                else:
                    changes[path] = None
                    del files[path]
        trash = ensure_inside(root, f"_state/trash/{identifier}.json")
        if trash.exists():
            changes[trash.relative_to(root).as_posix()] = None
        for trace in (Path(root) / "_state" / "searches").glob("*.json"):
            record = json.loads(trace.read_text(encoding="utf-8"))
            if any(c["id"] == identifier for c in record["candidates"]):
                changes[trace.relative_to(root).as_posix()] = None
        # All folder summaries are neutralized, including empty former folders.
        for readme in Path(root).rglob("README.md"):
            if "_state" not in readme.relative_to(root).parts:
                changes[readme.relative_to(root).as_posix()] = "Abstraction:\nPending maintenance.\nPending maintenance.\nPending maintenance.\n\nFiles:\n\nFolders:\n"
        changes.update(listings(files))
        commit_changes(root, changes)
        return {"id": identifier, "status": "forgotten"}
