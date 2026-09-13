from __future__ import annotations

import json
from pathlib import Path


class PathConfigError(ValueError):
    pass


def load_roots(config_path: str | Path | None = None, project_root: str | Path | None = None):
    if config_path is None:
        user_root = Path.home() / ".memoidx"
        configured_project = (Path(project_root) / ".memoidx").absolute() if project_root else find_project_root(Path.cwd())
        return user_root.resolve(), configured_project
    path = Path(config_path).resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        base = path.parent
        user = (base / data["user_root"]).resolve()
        project = (base / (project_root or data["project_root"]))
        if project.name != ".memoidx":
            project = project / ".memoidx"
        reject_links(project)
        reject_links(base / data["user_root"])
        project = project.resolve()
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise PathConfigError(f"cannot read config {path}: {exc}") from exc
    return user, project


def find_project_root(start: str | Path) -> Path | None:
    current = Path(start).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".memoidx").is_dir():
            return (candidate / ".memoidx").resolve()
    return None


def ensure_inside(root: str | Path, relative: str | Path) -> Path:
    reject_links(Path(root))
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise PathConfigError(f"path escapes root: {relative}")
    root = Path(root).resolve()
    reject_links(root / relative)
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PathConfigError(f"path escapes root: {relative}") from exc
    return target


def reject_links(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise PathConfigError(f"symlink or junction is forbidden: {part}")
