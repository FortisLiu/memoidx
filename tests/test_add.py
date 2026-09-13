import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from memoidx.clock import UTC_PLUS_8
from memoidx.edit import add_memory
from memoidx.format import parse_memory


class AddTests(unittest.TestCase):
    def test_add_creates_file_and_unit(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            request = {"request_id": "a-1", "file": "prefs.md", "content": "繁體中文", "retention": "normal", "source": "user"}
            result = add_memory(directory, request, lambda: datetime(2026, 9, 13, tzinfo=UTC_PLUS_8))
            self.assertEqual(add_memory(directory, request), result)
            with self.assertRaisesRegex(ValueError, "REQUEST_CONFLICT"):
                add_memory(directory, dict(request, content="different"))
            memory = parse_memory((Path(directory) / "prefs.md").read_text(encoding="utf-8"))
            self.assertEqual(len(memory.units), 1)
            self.assertEqual(memory.units[0].id, result["id"])


if __name__ == "__main__":
    unittest.main()
