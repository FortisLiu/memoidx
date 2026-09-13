import tempfile
import unittest
from pathlib import Path


class EnvironmentTests(unittest.TestCase):
    def test_can_write_inside_temporary_directory(self):
        # The managed test runner may not expose a system temp directory.
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            target = root / "sample.txt"

            target.write_text("假記憶", encoding="utf-8")

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "假記憶",
            )
