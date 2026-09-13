import tempfile
import unittest
from memoidx.init import initialize
from memoidx.edit import add_memory
from memoidx.doctor import doctor


class DoctorTests(unittest.TestCase):
    def test_reports_multiple_errors_without_rewriting_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = initialize(directory)
            add_memory(root, dict(request_id="d", file="a.md", content="body", retention="pinned", source="user"))
            original = (root / "a.md").read_bytes()
            (root / "duplicate.md").write_bytes(original)
            (root / "broken.md").write_text("invalid")
            reports = doctor(root)
            self.assertTrue(any("duplicate ID" in r["reason"] for r in reports))
            self.assertTrue(any(r.get("path") == "broken.md" for r in reports))
            self.assertEqual((root / "a.md").read_bytes(), original)
