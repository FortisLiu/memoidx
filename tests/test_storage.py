import tempfile
import unittest
from pathlib import Path

from memoidx.locking import root_lock
from memoidx.storage import atomic_write


class StorageTests(unittest.TestCase):
    def test_atomic_write_replaces_content(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            path = Path(directory) / "memory.md"
            atomic_write(path, "完整內容\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "完整內容\n")

    def test_root_lock_is_reentrant_for_sequential_operations(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            with root_lock(directory):
                marker = Path(directory) / "marker"
                marker.write_text("locked", encoding="utf-8")
            self.assertEqual(marker.read_text(encoding="utf-8"), "locked")


if __name__ == "__main__":
    unittest.main()
