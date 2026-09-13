import unittest
from datetime import datetime

from memoidx.clock import UTC_PLUS_8
from memoidx.hashes import file_summary_source_hash, unit_revision
from memoidx.models import MemoryFile, MemoryUnit


class HashTests(unittest.TestCase):
    def test_unit_revision_excludes_lut(self):
        first = MemoryUnit("u_a", datetime(2026, 1, 1, tzinfo=UTC_PLUS_8), "normal", "user", "same")
        second = MemoryUnit("u_a", datetime(2027, 1, 1, tzinfo=UTC_PLUS_8), "normal", "user", "same")
        self.assertEqual(unit_revision(first), unit_revision(second))
        second.content = "changed"
        self.assertNotEqual(unit_revision(first), unit_revision(second))

    def test_file_hash_depends_on_ids_and_content_only(self):
        t = datetime(2026, 1, 1, tzinfo=UTC_PLUS_8)
        one = MemoryFile("f_a", ("a", "b", "c"), t, "pending", [MemoryUnit("u_a", t, "normal", "x", "body")])
        two = MemoryFile("f_a", ("different", "summary", "text"), t, "pending", [MemoryUnit("u_a", t, "normal", "x", "body")])
        self.assertEqual(file_summary_source_hash(one), file_summary_source_hash(two))
        two.units[0].content = "changed"
        self.assertNotEqual(file_summary_source_hash(one), file_summary_source_hash(two))


if __name__ == "__main__":
    unittest.main()
