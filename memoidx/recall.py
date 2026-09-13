from .locking import root_lock
from .transactions import _recover, commit_changes
from .repository import locate, describe
from .retention import expired, settings
from .clock import now_utc
from .format import serialize_memory


def recall(root, identifier, clock=None):
    with root_lock(root):
        _recover(root)
        path, memory, unit = locate(root, identifier)
        now = now_utc(clock)
        if expired(unit, now, settings(root)["retention_months"]):
            raise ValueError("UNIT_EXPIRED")
        unit.latest_used_time = now
        memory.latest_used_time = max(u.latest_used_time for u in memory.units)
        commit_changes(root, {path: serialize_memory(memory)})
        return describe(path, unit)
