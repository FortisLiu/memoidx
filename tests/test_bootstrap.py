import tempfile
import unittest
import tomllib
from pathlib import Path

from memoidx.bootstrap import initialize_workspace


class BootstrapTests(unittest.TestCase):
    def test_native_scout_adapters_and_routing_preserved_on_rerun(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            initialize_workspace(workspace, user_root=base / "user")
            native = workspace / ".codex/agents/memoidx_scout.toml"
            config = tomllib.loads(native.read_text(encoding="utf-8"))
            self.assertEqual(config["name"], "memoidx_scout")
            self.assertIn("memoidx-scout.md", config["developer_instructions"])
            claude = workspace / ".claude/agents/memoidx-scout.md"
            self.assertIn("name: memoidx-scout", claude.read_text())
            contract = workspace / "memoidx-scout.md"
            self.assertIn("complete one requested memory\noperation", contract.read_text())
            native.write_text("# customized\n", encoding="utf-8")
            before = (workspace / "AGENTS.md").read_bytes()
            initialize_workspace(workspace, user_root=base / "user")
            self.assertEqual(native.read_text(), "# customized\n")
            self.assertEqual((workspace / "AGENTS.md").read_bytes(), before)
            self.assertEqual(before.count(b"<!-- memoidx-scout-routing-v2 -->"), 1)

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
