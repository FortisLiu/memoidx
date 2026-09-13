import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from memoidx.clock import UTC_PLUS_8
from memoidx.ids import new_unit_id, new_file_id
from memoidx.models import MemoryFile, MemoryUnit
from memoidx.format import parse_memory, serialize_memory, MemoryFormatError
from memoidx.storage import atomic_write
from memoidx.locking import root_lock
from memoidx.retention import cutoff
import subprocess
import sys


class FailureTests(unittest.TestCase):
    def test_process_termination_releases_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            code = "import sys,time; from memoidx.locking import root_lock\nwith root_lock(sys.argv[1]):\n print('locked',flush=True)\n time.sleep(30)\n"
            process = subprocess.Popen([sys.executable, "-c", code, directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.assertEqual(process.stdout.readline().strip(), "locked")
                with self.assertRaises(TimeoutError):
                    with root_lock(directory, timeout=0.1):
                        pass
            finally:
                process.terminate()
                process.communicate(timeout=5)
            with root_lock(directory):
                pass
    def memory(self, content):
        time = datetime(2026, 9, 13, microsecond=123456, tzinfo=UTC_PLUS_8)
        return MemoryFile(new_file_id(), ("a", "b", "c"), time, "pending", [MemoryUnit(new_unit_id(), time, "normal", "user", content)])

    def test_roundtrip_special_content(self):
        for content in ("", "\n", "中文\n\n", '"""', '    """\n', "def main():\n    pass\n", " tab\t"):
            with self.subTest(content=content):
                memory = self.memory(content)
                self.assertEqual(parse_memory(serialize_memory(memory)), memory)

    def test_bad_formats_have_locations(self):
        memory = self.memory("text")
        text = serialize_memory(memory)
        bad = [text.replace(memory.id, ""), text.replace(memory.id, "bad"),
               text.replace("2026-09-13", "2026-99-13"), text.replace("b\n", "", 1),
               text.rsplit('"""', 1)[0], text.replace("    text", "text")]
        for malformed in bad:
            with self.subTest(text=malformed):
                with self.assertRaises(MemoryFormatError) as caught:
                    parse_memory(malformed, "broken.md")
                self.assertEqual(caught.exception.filename, "broken.md")
                self.assertGreater(caught.exception.line, 0)

    def test_duplicate_ids_rejected(self):
        memory = self.memory("text")
        memory.units.append(memory.units[0])
        with self.assertRaisesRegex(MemoryFormatError, "duplicate ID"):
            serialize_memory(memory)

    def test_failed_replace_preserves_original(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.md"
            path.write_text("original")
            with patch("memoidx.storage.os.replace", side_effect=PermissionError("denied")):
                with self.assertRaises(PermissionError):
                    atomic_write(path, "replacement")
            self.assertEqual(path.read_text(), "original")
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_lock_timeout_does_not_mask_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with root_lock(directory):
                with self.assertRaises(TimeoutError):
                    with root_lock(directory, timeout=0):
                        self.fail("second lock was granted")
            with root_lock(directory):
                pass

    def test_calendar_cutoff(self):
        self.assertEqual(cutoff(datetime(2024, 8, 31, tzinfo=UTC_PLUS_8)).day, 29)
        self.assertEqual(cutoff(datetime(2025, 8, 31, tzinfo=UTC_PLUS_8)).day, 28)
