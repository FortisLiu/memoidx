import tempfile
import unittest
from pathlib import Path

from memoidx.transactions import create_transaction, pending_transactions
from memoidx.transactions import commit_changes, recover, require_recovered
from memoidx.locking import root_lock
from unittest.mock import patch


class TransactionTests(unittest.TestCase):
    def test_interrupted_cleanup_is_resumed_without_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with root_lock(root):
                with patch("memoidx.transactions._cleanup", side_effect=RuntimeError("cleanup interrupted")):
                    with self.assertRaises(RuntimeError):
                        commit_changes(root, {"a.md": "committed"})
            (root / "a.md").write_text("later edit")
            recover(root)
            self.assertEqual((root / "a.md").read_text(), "later edit")
            self.assertEqual(pending_transactions(root), [])

    def test_interrupted_commit_recovers_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "a.md").write_text("before", encoding="utf-8")
            def interrupt():
                raise RuntimeError("interruption")
            with root_lock(root):
                with self.assertRaises(RuntimeError):
                    commit_changes(root, {"a.md": "after", "b.md": "new"}, prepared_hook=interrupt)
            with self.assertRaisesRegex(ValueError, "RECOVERY_REQUIRED"):
                require_recovered(root)
            recover(root)
            recover(root)
            self.assertEqual((root / "a.md").read_text(), "after")
            self.assertEqual((root / "b.md").read_text(), "new")
            self.assertEqual(pending_transactions(root), [])

    def test_recovery_preserves_conflicting_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def interrupt():
                raise RuntimeError()
            with root_lock(root):
                with self.assertRaises(RuntimeError):
                    commit_changes(root, {"a.md": "after"}, prepared_hook=interrupt)
            (root / "a.md").write_text("someone else's edit")
            with self.assertRaisesRegex(ValueError, "REVISION_CONFLICT"):
                recover(root)
            self.assertEqual((root / "a.md").read_text(), "someone else's edit")

    def test_transaction_manifest_is_staged(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            transaction = create_transaction(directory, {"paths": ["a.md"], "before": {}, "after": {}})
            self.assertTrue((transaction / "manifest.json").exists())
            self.assertTrue((transaction / "staged").is_dir())
            self.assertEqual(pending_transactions(directory), [transaction])


if __name__ == "__main__":
    unittest.main()
