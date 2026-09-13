from .repository import memories
from .locking import root_lock
from .hashes import file_summary_source_hash


def tree(root):
    with root_lock(root):
        return [dict(path=p, units=len(m.units), summary="clean" if m.summary_of == file_summary_source_hash(m) else "stale") for p, m in memories(root)]
