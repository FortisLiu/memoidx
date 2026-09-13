from __future__ import annotations

import json
from pathlib import Path

from .clock import now_utc, serialize_datetime
from .format import parse_memory, serialize_memory
from .ids import new_file_id, new_unit_id
from .models import MemoryFile, MemoryUnit
from .storage import atomic_write
from .locking import root_lock
from .transactions import _recover, commit_changes
import hashlib
from .repository import locate, describe
from .hashes import unit_revision
from .paths import ensure_inside
from .folders import listings
from .repository import memories


def show_memory(root, identifier):
    with root_lock(root):
        path, memory, unit = locate(root, identifier)
        return describe(path, unit)


def update_memory(root, request):
    with root_lock(root):
        _recover(root)
        receipt = None
        signature = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if "request_id" in request:
            key = hashlib.sha256(str(request["request_id"]).encode()).hexdigest()
            receipt = "_state/requests/" + key + ".json"
            saved_path = Path(root) / receipt
            if saved_path.exists():
                saved = json.loads(saved_path.read_text(encoding="utf-8"))
                if saved["signature"] != signature:
                    raise ValueError("REQUEST_CONFLICT")
                return saved["result"]
        path, memory, unit = locate(root, request["id"])
        if unit_revision(unit) != request["expected_revision"]:
            raise ValueError("REVISION_CONFLICT")
        if not isinstance(request["content"], str):
            raise ValueError("content must be text")
        unit.content = request["content"]
        result = dict(id=unit.id, path=path, revision=unit_revision(unit), lut=serialize_datetime(unit.latest_used_time))
        changes = {path: serialize_memory(memory)}
        if receipt:
            changes[receipt] = json.dumps({"signature": signature, "result": result})
        commit_changes(root, changes)
        return result


def add_memory(root: str | Path, request: dict, clock=None) -> dict:
    with root_lock(root):
        _recover(root)
        return _add_memory(root, request, clock)


def _add_memory(root, request, clock):
    required = ("request_id", "file", "content", "retention", "source")
    missing = [key for key in required if key not in request]
    if missing:
        raise ValueError(f"missing fields: {', '.join(missing)}")
    if request["retention"] not in ("normal", "pinned"):
        raise ValueError("retention must be normal or pinned")
    root = Path(root).resolve()
    signature = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    request_key = hashlib.sha256(str(request["request_id"]).encode()).hexdigest()
    receipt_path = "_state/requests/" + request_key + ".json"
    receipt = root / receipt_path
    if receipt.exists():
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        if saved["signature"] != signature:
            raise ValueError("REQUEST_CONFLICT")
        return saved["result"]
    target = ensure_inside(root, request["file"])
    relative = target.relative_to(root)
    if "_state" in relative.parts or target.name == "README.md" or target.suffix != ".md":
        raise ValueError("INVALID_MEMORY_PATH")
    timestamp = now_utc(clock)
    if target.exists():
        memory = parse_memory(target.read_text(encoding="utf-8"), str(target))
    else:
        memory = MemoryFile(new_file_id(), ("待整理", "待整理", "待整理"), timestamp, "pending", [])
    source = request["source"]
    if not isinstance(source, str):
        source = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    unit = MemoryUnit(new_unit_id(), timestamp, request["retention"], source, request["content"])
    memory.units.append(unit)
    memory.latest_used_time = max((item.latest_used_time for item in memory.units))
    result = {"request_id": request["request_id"], "id": unit.id, "path": str(target), "lut": serialize_datetime(timestamp)}
    files = dict(memories(root))
    files[relative.as_posix()] = memory
    changes = listings(files)
    changes.update({relative.as_posix(): serialize_memory(memory),
                    receipt_path: json.dumps({"signature": signature, "result": result})})
    commit_changes(root, changes)
    return result
