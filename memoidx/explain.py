import json
from pathlib import Path
from .paths import ensure_inside
from .locking import root_lock
from .repository import locate
from .hashes import unit_revision
from .transactions import require_recovered


def explain(root, search_id, identifier):
    with root_lock(root):
        require_recovered(root)
        path = ensure_inside(root, f"_state/searches/{search_id}.json")
        trace = json.loads(path.read_text(encoding="utf-8"))
        for candidate in trace["candidates"]:
            if candidate["id"] == identifier:
                try:
                    _, _, unit = locate(root, identifier)
                    current = unit_revision(unit)
                except ValueError:
                    current = None
                return {**candidate, "search_id": search_id, "time": trace["time"],
                        "historical": current != candidate["revision"], "rule_version": 1}
        raise ValueError("CANDIDATE_NOT_FOUND")
