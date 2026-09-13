import argparse
import json
from pathlib import Path

from .init import initialize
from .paths import load_roots


def main():
    parser = argparse.ArgumentParser(
        prog="memoidx",
        description="Local memory for coding agents",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="memoidx 0.1.0",
    )
    parser.add_argument("--config")
    parser.add_argument("--json", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("protocol")
    subparsers.add_parser("reference")
    context_parser = subparsers.add_parser("context")
    context_parser.add_argument("query")
    context_parser.add_argument("--scope", choices=("user", "project", "both"), default="both")
    context_parser.add_argument("--limit", type=int, default=5)
    context_parser.add_argument("--max-chars", type=int, default=6000)
    for name in ("remember", "update"):
        child = subparsers.add_parser(name)
        child.add_argument("--scope", choices=("user", "project"), default="project")
        content = child.add_mutually_exclusive_group(required=True)
        content.add_argument("--content")
        content.add_argument("--stdin", action="store_true")
        if name == "remember":
            child.add_argument("--source", required=True)
            child.add_argument("--file", default="inbox.md")
            child.add_argument("--retention", choices=("normal", "pinned"), default="normal")
        else:
            child.add_argument("--id", required=True)
            child.add_argument("--expected-revision", required=True)
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--scope", choices=("user", "project"), required=True)
    for command in ("recover", "tree", "doctor", "search", "recall", "gc", "restore", "forget", "maintenance", "edit", "trash", "explain", "browse"):
        child = subparsers.add_parser(command)
        child.add_argument("--scope", choices=("user", "project"), default="project")
        if command == "search":
            child.add_argument("query")
        if command == "explain":
            child.add_argument("--search-id", required=True)
            child.add_argument("--id", required=True)
        if command == "browse":
            child.add_argument("kind", choices=("file", "folder"))
            child.add_argument("--path", required=True)
        if command in ("recall", "restore", "forget"):
            child.add_argument("--id", required=True)
        if command == "gc":
            child.add_argument("--dry-run", action="store_true")
            child.add_argument("--if-due", action="store_true")
        if command == "edit":
            child.add_argument("action", choices=("add", "show", "update"))
            child.add_argument("--input")
            child.add_argument("--id")
        if command == "maintenance":
            child.add_argument("action", choices=("plan", "read", "apply", "check", "folders", "read-folder", "apply-folder"))
            child.add_argument("--file")
            child.add_argument("--folder", default=".")
            child.add_argument("--input")
        if command == "trash":
            child.add_argument("action", choices=("list",))
    args = parser.parse_args()
    if args.command:
        try:
            result = dispatch(args)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False))
            return 1
        if args.json or not isinstance(result, str):
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(result)
    return 0


def dispatch(args):
        if args.command in ("protocol", "reference"):
            from importlib.resources import files
            name = "protocol.md" if args.command == "protocol" else "memoidx-cli.md"
            return files("memoidx").joinpath(name).read_text(encoding="utf-8")
        from . import edit, maintenance
        from .transactions import recover
        from .tree import tree
        from .doctor import doctor
        from .search import search
        from .recall import recall
        from .gc import collect
        from .restore import restore
        from .forget import forget
        from .folders import refresh
        user_root, project_root = load_roots(args.config)
        if args.command == "context":
            from .high_frequency import context, render_context
            roots = {"user": user_root, "project": project_root}
            if args.scope != "both":
                roots = {args.scope: roots[args.scope]}
            result = context(roots, args.query, limit=args.limit, max_chars=args.max_chars)
            return result if args.json else render_context(result)
        root = user_root if args.scope == "user" else project_root
        if root is None:
            raise ValueError("PROJECT_ROOT_NOT_FOUND: specify --config")
        if args.command == "init":
            return str(initialize(root))
        if not root.is_dir():
            raise ValueError("ROOT_NOT_INITIALIZED")
        if args.command in ("remember", "update"):
            import sys
            content = sys.stdin.read() if args.stdin else args.content
            if args.command == "remember":
                from .high_frequency import remember
                return remember(root, content, args.source, file=args.file, retention=args.retention)
            return edit.update_memory(root, {"id": args.id,
                "expected_revision": args.expected_revision, "content": content})
        if args.command == "recover":
            recover(root)
            return {"status": "recovered"}
        if args.command == "tree":
            return tree(root)
        if args.command == "explain":
            from .explain import explain
            return explain(root, args.search_id, args.id)
        if args.command == "browse":
            from .locking import root_lock
            from .paths import ensure_inside
            from .repository import memories
            from .transactions import require_recovered
            with root_lock(root):
                require_recovered(root)
                if args.kind == "folder":
                    from .folders import folder_view
                    from .clock import now_utc
                    description, fresh = folder_view(root, args.path, dict(memories(root)), now_utc())
                    return {"summary": description, "status": "clean" if fresh else "stale"}
                for path, memory in memories(root):
                    if path == args.path:
                        from .clock import now_utc
                        from .retention import expired, settings
                        from .hashes import file_summary_source_hash
                        now = now_utc()
                        valid = [u for u in memory.units if not expired(u, now, settings(root)["retention_months"])]
                        clean = len(valid) == len(memory.units) and memory.summary_of == file_summary_source_hash(memory)
                        return {"summary": memory.summary if clean else ("Pending maintenance",) * 3, "ids": [u.id for u in valid]}
                raise ValueError("FILE_NOT_FOUND")
        if args.command == "doctor":
            return doctor(root)
        if args.command == "search":
            return search({args.scope: root}, args.query)
        if args.command == "recall":
            return recall(root, args.id)
        if args.command == "gc":
            return collect(root, dry_run=args.dry_run, if_due=args.if_due)
        if args.command == "restore":
            return restore(root, args.id)
        if args.command == "forget":
            return forget(root, args.id)
        if args.command == "trash":
            return [{"id": p.stem} for p in sorted((root / "_state" / "trash").glob("*.json"))]
        if args.command == "edit":
            if args.action == "show":
                return edit.show_memory(root, args.id)
            if not args.input:
                raise ValueError("--input is required")
            request = json.loads(Path(args.input).read_text(encoding="utf-8"))
            if request.get("scope", args.scope) != args.scope:
                raise ValueError("SCOPE_MISMATCH")
            return edit.add_memory(root, request) if args.action == "add" else edit.update_memory(root, request)
        if args.command == "maintenance":
            if args.action == "read-folder":
                from .folders import read_folder
                return read_folder(root, args.folder)
            if args.action == "apply-folder":
                from .folders import apply_folder
                request = json.loads(Path(args.input).read_text(encoding="utf-8"))
                return apply_folder(root, request["folder"], request["expected_source_hash"], request["summary"])
            if args.action in ("plan", "check"):
                return maintenance.plan(root)
            if args.action == "read":
                return maintenance.read(root, args.file)
            if args.action == "folders":
                refresh(root)
                return {"status": "refreshed"}
            request = json.loads(Path(args.input).read_text(encoding="utf-8"))
            return maintenance.apply(root, request["file"], request["expected_source_hash"], request["summary"])
