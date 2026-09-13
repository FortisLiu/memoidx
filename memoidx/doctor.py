from .repository import memories
from .locking import root_lock
from .hashes import file_summary_source_hash
from pathlib import Path
import json
from .format import parse_memory
from .transactions import pending_transactions
from .paths import ensure_inside
from .folders import listings


def doctor(root):
    reports = []
    root = Path(root)
    if not root.is_dir():
        return [{"level": "ERROR", "reason": "ROOT_NOT_INITIALIZED"}]
    with root_lock(root):
        seen = set()
        files = {}
        config = root / "config.json"
        try:
            json.loads(config.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            reports.append({"level": "ERROR", "path": "config.json", "reason": str(exc)})
        if pending_transactions(root):
            reports.append({"level": "ERROR", "reason": "RECOVERY_REQUIRED"})
            return reports
        for target in sorted(root.rglob("*.md")):
            path = target.relative_to(root).as_posix()
            if "_state" in target.relative_to(root).parts or target.name == "README.md":
                continue
            try:
                ensure_inside(root, path)
                memory = parse_memory(target.read_text(encoding="utf-8"), path)
                files[path] = memory
                for identifier in [memory.id, *(u.id for u in memory.units)]:
                    if identifier in seen:
                        reports.append({"level": "ERROR", "path": path, "reason": "duplicate ID: " + identifier})
                    seen.add(identifier)
                if memory.latest_used_time != max(u.latest_used_time for u in memory.units):
                    reports.append({"level": "ERROR", "path": path, "reason": "file LUT mismatch"})
                if memory.summary_of != file_summary_source_hash(memory):
                    reports.append({"level": "WARN", "path": path, "reason": "summary stale"})
            except (ValueError, OSError) as exc:
                reports.append({"level": "ERROR", "path": path, "reason": str(exc)})
        for path, expected in listings(files).items():
            target = root / path
            if not target.exists():
                reports.append({"level": "ERROR", "path": path, "reason": "missing README"})
                continue
            actual = target.read_text(encoding="utf-8").splitlines()[4:]
            if actual != expected.splitlines()[4:]:
                reports.append({"level": "WARN", "path": path, "reason": "README listing mismatch"})
    return reports
