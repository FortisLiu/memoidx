import tempfile
import unittest
from pathlib import Path

from memoidx.bootstrap import initialize_workspace


class BootstrapTests(unittest.TestCase):
    def test_workspace_bootstrap_preserves_and_augments_existing_agent_files(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            workspace = Path(directory)
            user_root = workspace / "user" / ".memoidx"
            (workspace / "MemoIdx.md").write_text("old protocol\n", encoding="utf-8")
            agents = workspace / "AGENTS.md"
            agents.write_text("custom instructions\n", encoding="utf-8")
            result = initialize_workspace(workspace, user_root=user_root)
            self.assertTrue((workspace / ".memoidx" / "config.json").exists())
            self.assertEqual((workspace / "MemoIdx.md").read_text(encoding="utf-8"), "old protocol\n")
            self.assertEqual(result["files"]["AGENTS.md"], "updated")
            self.assertIn("MemoIdx.md", agents.read_text(encoding="utf-8"))
            again = initialize_workspace(workspace, user_root=user_root)
            self.assertIn("custom instructions", agents.read_text(encoding="utf-8"))
            self.assertIn("MemoIdx.md", agents.read_text(encoding="utf-8"))
            self.assertEqual(again["files"]["AGENTS.md"], "kept")


if __name__ == "__main__":
    unittest.main()
