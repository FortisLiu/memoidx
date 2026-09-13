from pathlib import PurePosixPath
from .repository import memories
from .locking import root_lock
from .transactions import _recover, commit_changes
from pathlib import Path
from .paths import ensure_inside
from .hashes import _digest, file_summary_source_hash
from .retention import expired, settings
from .clock import now_utc
import json


def folder_source(root, folder, files):
    prefix = PurePosixPath(folder)
    data = []
    for path, memory in sorted(files.items()):
        if PurePosixPath(path).is_relative_to(prefix):
            data.append({"path": path, "content": file_summary_source_hash(memory),
                         "summary": memory.summary, "summary_of": memory.summary_of})
    return _digest(data)


def folder_view(root, folder, files, now):
    relative = str(PurePosixPath(folder) / "README.md")
    path = ensure_inside(root, relative)
    record = Path(root) / "_state" / "folders" / (_digest(folder) + ".json")
    neutral = ("Pending maintenance",) * 3
    if not record.exists() or not path.exists():
        return neutral, False
    saved = json.loads(record.read_text(encoding="utf-8"))
    text = path.read_text(encoding="utf-8")
    clean = saved["source_hash"] == folder_source(root, folder, files) and saved["readme_hash"] == _digest(text)
    for name, memory in files.items():
        if PurePosixPath(name).is_relative_to(PurePosixPath(folder)):
            clean = clean and memory.summary_of == file_summary_source_hash(memory)
            clean = clean and not any(expired(u, now, settings(root)["retention_months"]) for u in memory.units)
    return (tuple(text.splitlines()[1:4]), True) if clean else (neutral, False)


def read_folder(root, folder):
    with root_lock(root):
        files = dict(memories(root))
        ensure_inside(root, folder)
        return {"folder": folder, "source_hash": folder_source(root, folder, files),
                "files": [{"path": p, "summary": m.summary} for p, m in files.items() if PurePosixPath(p).is_relative_to(PurePosixPath(folder))]}


def apply_folder(root, folder, expected_source_hash, summary):
    if len(summary) != 3 or any(not isinstance(s, str) or not s or "\n" in s or "\r" in s for s in summary):
        raise ValueError("summary must contain three nonempty lines")
    with root_lock(root):
        _recover(root)
        files = dict(memories(root))
        if folder_source(root, folder, files) != expected_source_hash:
            raise ValueError("REVISION_CONFLICT")
        relative = str(PurePosixPath(folder) / "README.md")
        ensure_inside(root, relative)
        skeleton = listings(files).get(relative)
        if skeleton is None:
            raise ValueError("FOLDER_NOT_FOUND")
        text = "\n".join(["Abstraction:", *summary, *skeleton.splitlines()[4:]]) + "\n"
        record = "_state/folders/" + _digest(folder) + ".json"
        commit_changes(root, {relative: text, record: json.dumps({"source_hash": expected_source_hash, "readme_hash": _digest(text)})})
        return {"folder": folder, "status": "clean"}


def listings(files):
    """Build neutral directory indexes for the proposed set of memory paths."""
    folders = {"."}
    for path in files:
        folders.update(str(p) for p in PurePosixPath(path).parents)
    result = {}
    for folder in folders:
        here = PurePosixPath(folder)
        names = sorted(PurePosixPath(p).name for p in files if PurePosixPath(p).parent == here)
        children = sorted(PurePosixPath(p).name for p in folders if p != "." and PurePosixPath(p).parent == here)
        result[str(here / "README.md")] = "Abstraction:\nPending maintenance.\nPending maintenance.\nPending maintenance.\n\nFiles:\n" + "".join(f"- {n}\n" for n in names) + "\nFolders:\n" + "".join(f"- {n}/\n" for n in children)
    return result


def refresh(root):
    with root_lock(root):
        _recover(root)
        commit_changes(root, listings(dict(memories(root))))
