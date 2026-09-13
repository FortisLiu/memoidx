from .locking import root_lock
from .repository import memories
from .hashes import file_summary_source_hash, unit_revision
from .retention import expired, settings
from .clock import now_utc
from .clock import serialize_datetime
from .storage import atomic_write
from uuid import uuid4
from pathlib import Path
import json
from pathlib import PurePosixPath
from .folders import folder_view


def search(roots, query, clock=None):
    words = list(dict.fromkeys(query.casefold().split()))
    now = now_utc(clock)
    results = []
    search_id = str(uuid4())
    for scope, root in roots.items():
        if root is None:
            continue
        with root_lock(root):
            files = dict(memories(root))
            for path, memory in files.items():
                valid = [u for u in memory.units if not expired(u, now, settings(root)["retention_months"])]
                clean = len(valid) == len(memory.units) and memory.summary_of == file_summary_source_hash(memory)
                summary = memory.summary if clean else ("Pending maintenance",) * 3
                for unit in valid:
                    body_hits = [w for w in words if w in unit.content.casefold()]
                    summary_hits = [w for w in words if clean and w in "\n".join(summary).casefold()]
                    folder_hits = set()
                    for parent in PurePosixPath(path).parents:
                        description, fresh = folder_view(root, str(parent), files, now)
                        if fresh:
                            folder_hits.update(w for w in words if w in "\n".join(description).casefold())
                    score = len(body_hits) * 4 + len(summary_hits) * 2 + len(folder_hits)
                    if score:
                        results.append(dict(id=unit.id, scope=scope, path=path, summary=summary,
                                            search_id=search_id, revision=unit_revision(unit),
                                            snippet=unit.content[:160], score=score,
                                            body_hits=body_hits, summary_hits=summary_hits, folder_hits=sorted(folder_hits)))
            candidates = [{k: v for k, v in r.items() if k not in ("snippet", "summary")} for r in results if r["scope"] == scope]
            atomic_write(Path(root) / "_state" / "searches" / (search_id + ".json"),
                         json.dumps({"time": serialize_datetime(now), "candidates": candidates}, ensure_ascii=False))
    return sorted(results, key=lambda r: (-r["score"], r["scope"] != "project", r["path"], r["id"]))[:10]
