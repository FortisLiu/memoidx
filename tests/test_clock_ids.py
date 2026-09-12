import unittest
from datetime import datetime
from uuid import UUID

from memoidx.clock import UTC_PLUS_8, now_utc, parse_datetime, serialize_datetime
from memoidx.ids import new_file_id, new_unit_id


class ClockAndIdsTests(unittest.TestCase):
    def test_ids_are_unique_and_have_correct_prefixes(self):
        unit_ids = [new_unit_id() for _ in range(1000)]
        file_ids = [new_file_id() for _ in range(1000)]
        self.assertEqual(len(set(unit_ids)), 1000)
        self.assertEqual(len(set(file_ids)), 1000)
        for value in unit_ids:
            self.assertTrue(value.startswith("u_"))
            UUID(value[2:])
        for value in file_ids:
            self.assertTrue(value.startswith("f_"))
            UUID(value[2:])

    def test_fixed_clock_is_repeatable(self):
        fixed = datetime(2026, 9, 13, tzinfo=UTC_PLUS_8)
        clock = lambda: fixed
        self.assertEqual(now_utc(clock), fixed)
        self.assertEqual(now_utc(clock), fixed)

    def test_datetime_round_trip(self):
        fixed = datetime(2026, 9, 13, tzinfo=UTC_PLUS_8)
        encoded = serialize_datetime(fixed)
        self.assertEqual(encoded, "2026-09-13T00:00:00+08:00")
        self.assertEqual(parse_datetime(encoded), fixed)


if __name__ == "__main__":
    unittest.main()
