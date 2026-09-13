from .locking import root_lock
from .repository import memories, describe
from .hashes import file_summary_source_hash
from .transactions import _recover, commit_changes
from .format import serialize_memory


def plan(root):
    with root_lock(root):
        return [path for path, m in memories(root) if m.summary_of != file_summary_source_hash(m)]


def read(root, path):
    with root_lock(root):
        for name, memory in memories(root):
            if name == path:
                return {"file": path, "source_hash": file_summary_source_hash(memory),
                        "units": [describe(path, u) for u in memory.units]}
    raise ValueError("FILE_NOT_FOUND")


def apply(root, path, expected_source_hash, summary):
    if not isinstance(summary, (list, tuple)) or len(summary) != 3 or any(not isinstance(s, str) or not s or "\n" in s or "\r" in s for s in summary):
        raise ValueError("summary must contain three nonempty lines")
    with root_lock(root):
        _recover(root)
        for name, memory in memories(root):
            if name == path:
                if file_summary_source_hash(memory) != expected_source_hash:
                    raise ValueError("REVISION_CONFLICT")
                memory.summary = tuple(summary)
                memory.summary_of = expected_source_hash
                commit_changes(root, {path: serialize_memory(memory)})
                return {"file": path, "status": "clean"}
    raise ValueError("FILE_NOT_FOUND")
