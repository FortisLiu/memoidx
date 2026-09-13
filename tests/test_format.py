import unittest
from datetime import datetime

from memoidx.clock import UTC_PLUS_8
from memoidx.format import MemoryFormatError, parse_memory, serialize_memory
from memoidx.models import MemoryFile, MemoryUnit
from memoidx.ids import new_file_id, new_unit_id


class FormatTests(unittest.TestCase):
    def test_round_trip_preserves_content(self):
        t = datetime(2026, 9, 13, tzinfo=UTC_PLUS_8)
        memory = MemoryFile(new_file_id(), ("topic", "scope", "keywords"), t, "project", [
            MemoryUnit(new_unit_id(), t, "normal", "user", "第一行\n    保留縮排\n第三行"),
            MemoryUnit(new_unit_id(), t, "pinned", "agent", "最後一張卡"),
        ])
        self.assertEqual(parse_memory(serialize_memory(memory)), memory)

    def test_invalid_inputs_report_line_and_reason(self):
        cases = [
            ("Abstraction:\na\nb\nc\nfile id: f\nLatest used time: bad\nSummary of: x\n\nMemory id: u\nLatest used time: bad", "invalid datetime"),
            ("Abstraction:\na\nb\nfile id: f", "summary must contain three lines"),
        ]
        for text, reason in cases:
            with self.assertRaisesRegex(MemoryFormatError, reason):
                parse_memory(text, "sample.memo")


if __name__ == "__main__":
    unittest.main()
