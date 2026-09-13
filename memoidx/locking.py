from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from .paths import reject_links


@contextmanager
def root_lock(root: str | Path, timeout: float = 5.0):
    """Acquire an OS-level exclusive lock for a memory root."""
    lock_path = Path(root) / "_state" / ".lock"
    reject_links(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    deadline = time.monotonic() + timeout
    acquired = False
    try:
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (OSError, IOError):
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"lock timeout: {lock_path}")
                time.sleep(0.05)
        yield
    finally:
        try:
            if acquired and os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            elif acquired:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
