import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from memoidx.clock import UTC_PLUS_8
from memoidx.init import initialize
from memoidx.edit import add_memory, show_memory, update_memory
from memoidx.search import search
from memoidx.recall import recall
from memoidx import maintenance
from memoidx.folders import refresh
from memoidx.tree import tree
from memoidx.gc import collect
from memoidx.restore import restore
from memoidx.forget import forget
from memoidx.doctor import doctor
from memoidx.transactions import recover, commit_changes
from memoidx.locking import root_lock


class EndToEndTests(unittest.TestCase):
    def test_memory_lifecycle_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = initialize(Path(directory) / "project" / ".memoidx")
            user = initialize(Path(directory) / "user" / ".memoidx")
            time = datetime(2026, 1, 13, tzinfo=UTC_PLUS_8)
            clock = lambda: time
            marker = "MEMOIDX_FORGET_TEST_8F31"
            ids = []
            for i, content in enumerate(("繁體中文", marker, "pinned card")):
                request = dict(request_id=str(i), file="偏好 folder/answers.md", content=content,
                               retention="pinned" if i == 2 else "normal", source="user")
                result = add_memory(root, request, clock)
                self.assertEqual(result, add_memory(root, request, clock))
                ids.append(result["id"])
            first = show_memory(root, ids[0])
            update_memory(root, dict(id=ids[0], expected_revision=first["revision"], content="繁體中文 回答"))
            with self.assertRaisesRegex(ValueError, "REVISION_CONFLICT"):
                update_memory(root, dict(id=ids[0], expected_revision=first["revision"], content="bad"))
            snapshots = [show_memory(root, i)["lut"] for i in ids]
            self.assertEqual(search({"project": root, "user": user}, "繁體", clock)[0]["id"], ids[0])
            self.assertEqual(snapshots, [show_memory(root, i)["lut"] for i in ids])
            time = datetime(2026, 2, 13, tzinfo=UTC_PLUS_8)
            recall(root, ids[0], clock)
            self.assertEqual(snapshots[1:], [show_memory(root, i)["lut"] for i in ids[1:]])
            path = "偏好 folder/answers.md"
            source = maintenance.read(root, path)
            maintenance.apply(root, path, source["source_hash"], ["偏好", marker, "回答"])
            self.assertEqual(maintenance.plan(root), [])
            refresh(root)
            self.assertEqual(tree(root)[0]["units"], 3)
            time = datetime(2026, 8, 14, tzinfo=UTC_PLUS_8)
            before = (root / path).read_bytes()
            self.assertEqual(len(collect(root, clock, dry_run=True)), 2)
            self.assertEqual((root / path).read_bytes(), before)
            collect(root, clock)
            self.assertEqual(search({"project": root}, marker, clock), [])
            restore(root, ids[0], clock)
            self.assertEqual(collect(root, clock), [])
            def interrupt():
                raise RuntimeError("power loss")
            with root_lock(root):
                with self.assertRaises(RuntimeError):
                    commit_changes(root, {"README.md": "Abstraction:\n" + marker + "\nb\nc\n"}, prepared_hook=interrupt)
            forget(root, ids[1])
            recover(root)
            self.assertFalse(any(r["level"] == "ERROR" for r in doctor(root)))
            for file in root.rglob("*"):
                if file.is_file():
                    self.assertNotIn(marker.encode(), file.read_bytes(), str(file))
            self.assertEqual(len(tree(root)), 1)
            self.assertEqual(tree(root)[0]["units"], 2)


if __name__ == "__main__":
    unittest.main()
