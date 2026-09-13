from __future__ import annotations

import json
from pathlib import Path
from .paths import reject_links


def initialize(root: str | Path) -> Path:
    reject_links(root)
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "_state" / "transactions").mkdir(parents=True, exist_ok=True)
    (root / "_state" / "trash").mkdir(parents=True, exist_ok=True)
    readme = root / "README.md"
    for child in (readme, root / "config.json", root / "_state", root / "_state" / "transactions", root / "_state" / "trash"):
        reject_links(child)
    if not readme.exists():
        readme.write_text("Abstraction:\n待整理。\n待整理。\n待整理。\n\nFiles:\n", encoding="utf-8", newline="\n")
    config = root / "config.json"
    if not config.exists():
        config.write_text(json.dumps({"retention_months": 6, "trash_days": 30}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return root
