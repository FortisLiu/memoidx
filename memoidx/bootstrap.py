"""User-facing workspace bootstrap for MemoIdx."""

from __future__ import annotations

import json
import re
from pathlib import Path
from importlib.resources import files
from .paths import reject_links
from .storage import atomic_write

from .init import initialize
from .scout import SCOUT_FILES, ROUTING, native_templates


def _ensure_memo_file(path: Path) -> str:
    if path.exists():
        return "kept"
    name = "protocol.md" if path.name == "MemoIdx.md" else path.name
    atomic_write(path, files("memoidx").joinpath(name).read_text(encoding="utf-8"))
    return "created"


def _ensure_agent_file(path: Path) -> str:
    instructions = ("# MemoIdx integration\n\n@MemoIdx.md\n" if path.name == "CLAUDE.md"
                    else "# MemoIdx integration\n\nRead and follow `MemoIdx.md` before using persistent memory.\n")
    if not path.exists():
        atomic_write(path, instructions)
        return "created"
    content = path.read_text(encoding="utf-8")
    if re.search(r"(?im)^\s*@MemoIdx\.md\s*$|\b(?:read|follow|consult)\b[^\n]*MemoIdx\.md|(?:讀取|閱讀|遵循)[^\n]*MemoIdx\.md", content):
        return "kept"
    separator = "\n" if content.endswith("\n") else "\n\n"
    atomic_write(path, content + separator + instructions)
    return "updated"


def initialize_workspace(workspace: str | Path | None = None, *, user_root=None) -> dict:
    workspace = Path(workspace or Path.cwd()).absolute()
    user_root = Path(user_root or (Path.home() / ".memoidx")).absolute()
    project_root = workspace / ".memoidx"
    for path in (workspace, user_root, project_root, project_root / "roots.json",
                 project_root / "config.json", *(workspace / name for name in
                 ("MemoIdx.md", "memoidx-cli.md", "AGENTS.md", "CLAUDE.md", *SCOUT_FILES))):
        reject_links(path)
    for name in ("MemoIdx.md", "memoidx-cli.md", "AGENTS.md", "CLAUDE.md", *SCOUT_FILES):
        path = workspace / name
        if path.exists() and not path.is_file():
            raise ValueError("INSTRUCTION_NOT_FILE: " + str(path))
    initialize(user_root)
    initialize(project_root)
    config = project_root / "roots.json"
    if not config.exists():
        atomic_write(config, json.dumps({"user_root": str(user_root.resolve()), "project_root": "."}, indent=2) + "\n")
    result = {
        "workspace": str(workspace),
        "user_root": str(user_root),
        "project_root": str(project_root),
        "note": "Existing documents are preserved; use memoidx protocol/reference for installed documentation.",
        "files": {
            "MemoIdx.md": _ensure_memo_file(workspace / "MemoIdx.md"),
            "memoidx-cli.md": _ensure_memo_file(workspace / "memoidx-cli.md"),
            "AGENTS.md": _ensure_agent_file(workspace / "AGENTS.md"),
            "CLAUDE.md": _ensure_agent_file(workspace / "CLAUDE.md"),
        },
    }
    result["files"]["memoidx-scout.md"] = _ensure_memo_file(workspace / "memoidx-scout.md")
    for name, content in native_templates().items():
        path = workspace / name
        status = "kept" if path.exists() else "created"
        if not path.exists():
            atomic_write(path, content)
        result["files"][name] = status
    for name in ("AGENTS.md", "CLAUDE.md"):
        path = workspace / name
        content = path.read_text(encoding="utf-8")
        if "<!-- memoidx-scout-routing-v1 -->" not in content:
            atomic_write(path, content + "\n" + ROUTING)
            if result["files"][name] == "kept":
                result["files"][name] = "updated"
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="memoidx-init")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--user-root")
    args = parser.parse_args()
    try:
        result = initialize_workspace(args.workspace, user_root=args.user_root)
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
