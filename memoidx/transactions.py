from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4
import hashlib
import shutil

from .storage import atomic_write
from .paths import ensure_inside
from .locking import root_lock


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def require_recovered(root):
    if pending_transactions(root):
        raise ValueError("RECOVERY_REQUIRED")


def _recover(root):
    for directory in pending_transactions(root):
        ensure_inside(root, directory.relative_to(root))
        completed = Path(root) / "_state" / "completed" / (directory.name + ".json")
        if completed.exists() or not (directory / "manifest.json").exists():
            _cleanup(root, directory)
            continue
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("state") != "prepared":
            raise ValueError("RECOVERY_REQUIRED: invalid transaction manifest")
        entries = manifest["entries"]
        for entry in entries:
            target = ensure_inside(root, entry["path"])
            if fingerprint(target) not in (entry["before"], entry["after"]):
                raise ValueError("REVISION_CONFLICT: " + entry["path"])
            if entry["after"] is not None:
                staged = ensure_inside(directory / "staged", entry["stage"])
                if fingerprint(staged) != entry["after"]:
                    raise ValueError("CORRUPT_TRANSACTION")
        for entry in entries:
            target = ensure_inside(root, entry["path"])
            if fingerprint(target) == entry["after"]:
                continue
            if entry["after"] is None:
                target.unlink()
            else:
                staged = ensure_inside(directory / "staged", entry["stage"])
                atomic_write(target, staged.read_text(encoding="utf-8"))
        atomic_write(Path(root) / "_state" / "completed" / (directory.name + ".json"),
                     json.dumps({"operation_id": directory.name, "state": "complete"}))
        _cleanup(root, directory)


def _cleanup(root, directory):
    # Only a single validated generated transaction directory is removable.
    from uuid import UUID
    UUID(directory.name)
    parent = ensure_inside(root, "_state/transactions")
    if directory.parent.resolve() != parent.resolve():
        raise ValueError("INVALID_TRANSACTION_PATH")
    for child in directory.rglob("*"):
        ensure_inside(root, child.relative_to(root))
    shutil.rmtree(directory)


def recover(root):
    with root_lock(root):
        _recover(root)


def commit_changes(root, changes, *, prepared_hook=None):
    """Commit relative text paths (None means deletion); caller holds root lock."""
    _recover(root)
    directory = Path(root) / "_state" / "transactions" / str(uuid4())
    (directory / "staged").mkdir(parents=True)
    entries = []
    for index, (relative, content) in enumerate(changes.items()):
        target = ensure_inside(root, relative)
        stage = str(index)
        after = None
        if content is not None:
            atomic_write(directory / "staged" / stage, content)
            after = fingerprint(directory / "staged" / stage)
        entries.append({"path": relative, "before": fingerprint(target),
                        "after": after, "stage": stage})
    atomic_write(directory / "manifest.json", json.dumps({"state": "prepared", "entries": entries}))
    if prepared_hook:
        prepared_hook()
    _recover(root)


def create_transaction(root: str | Path, manifest: dict) -> Path:
    directory = Path(root) / "_state" / "transactions" / str(uuid4())
    (directory / "staged").mkdir(parents=True, exist_ok=False)
    (directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    return directory


def pending_transactions(root: str | Path) -> list[Path]:
    directory = Path(root) / "_state" / "transactions"
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.iterdir() if path.is_dir())
