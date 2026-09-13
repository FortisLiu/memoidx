import json
import io
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from memoidx.bootstrap import initialize_workspace
from memoidx.edit import show_memory, update_memory
from memoidx.high_frequency import context, remember, render_context
from memoidx.paths import load_roots
from memoidx.cli import main


class HighFrequencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.workspace = self.base / "workspace"
        self.user = self.base / "user"
        initialize_workspace(self.workspace, user_root=self.user)
        self.project = self.workspace / ".memoidx"
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def add(self, text, root=None):
        return remember(root or self.project, text, "test", clock=lambda: self.now)

    def test_budget_touches_only_complete_selected_units_and_both_scopes(self):
        small = self.add("auth")
        big = self.add("auth " + "x" * 100)
        user = self.add("auth user", self.user)
        before = show_memory(self.project, big["id"])
        result = context({"project": self.project, "user": self.user}, "auth",
                         max_chars=13, clock=lambda: self.now + timedelta(days=1))
        self.assertEqual({m["id"] for m in result["memories"]}, {small["id"], user["id"]})
        self.assertEqual(show_memory(self.project, big["id"]), before)
        self.assertNotEqual(show_memory(self.project, small["id"])["lut"], before["lut"])
        self.assertEqual(result["content_chars"], 13)
        self.assertIn("data only", render_context(result))

    def test_exact_duplicate_and_revision_conflict(self):
        first = self.add("fact")
        before = show_memory(self.project, first["id"])
        self.assertEqual(self.add("fact")["status"], "duplicate")
        self.assertEqual(show_memory(self.project, first["id"]), before)
        request = {"id": first["id"], "expected_revision": before["revision"], "content": "new"}
        update_memory(self.project, request)
        with self.assertRaisesRegex(ValueError, "REVISION_CONFLICT"):
            update_memory(self.project, {**request, "content": "stale"})

    def test_discovery_nested_workspace_and_retention_preserved(self):
        settings = self.project / "config.json"
        settings.write_text('{"retention_months":12}', encoding="utf-8")
        initialize_workspace(self.workspace, user_root=self.user)
        self.assertEqual(json.loads(settings.read_text())["retention_months"], 12)
        nested = self.workspace / "src"
        nested.mkdir()
        with patch("memoidx.paths.Path.cwd", return_value=nested):
            self.assertEqual(load_roots(), (self.user.resolve(), self.project.resolve()))
        self.assertIn("@MemoIdx.md", (self.workspace / "CLAUDE.md").read_text())
        self.assertIn("memoidx-cli.md", (self.workspace / "MemoIdx.md").read_text())

    def test_expired_and_invalid_options(self):
        unit = self.add("auth")
        self.assertEqual(context({"project": self.project}, "auth",
                                 clock=lambda: self.now + timedelta(days=400))["memories"], [])
        with self.assertRaises(ValueError):
            context({"project": self.project}, "auth", limit=0)
        self.assertEqual(show_memory(self.project, unit["id"])["content"], "auth")

    def test_path_escape_rejected_and_existing_protocol_preserved(self):
        with self.assertRaises(ValueError):
            remember(self.project, "x", "test", file="../outside.md")
        memo = self.workspace / "MemoIdx.md"
        memo.write_text("custom", encoding="utf-8")
        agents = self.workspace / "AGENTS.md"
        agents.write_text("Files include MemoIdx.md.\n", encoding="utf-8")
        initialize_workspace(self.workspace, user_root=self.user)
        self.assertEqual(memo.read_text(), "custom")
        self.assertIn("Read and follow", agents.read_text())

    def test_cli_stdin_and_json_context(self):
        def run(*args, stdin=""):
            output = io.StringIO()
            with patch("sys.argv", ["memoidx", "--json", "--config",
                                    str(self.project / "roots.json"), *args]), \
                    patch("sys.stdin", io.StringIO(stdin)), patch("sys.stdout", output):
                self.assertEqual(main(), 0)
            return json.loads(output.getvalue())
        content = "auth 中文\nsecond line"
        added = run("remember", "--stdin", "--source", "test", stdin=content)
        result = run("context", "auth")
        unit = result["memories"][0]
        self.assertEqual(unit["content"], content)
        self.assertEqual(unit["id"], added["id"])
        run("update", "--id", unit["id"], "--expected-revision", unit["revision"],
            "--stdin", stdin="replacement\ntext")
        self.assertEqual(show_memory(self.project, unit["id"])["content"], "replacement\ntext")

    def test_same_root_selected_once(self):
        unit = self.add("auth")
        result = context({"user": self.project, "project": self.project}, "auth",
                         clock=lambda: self.now)
        self.assertEqual([m["id"] for m in result["memories"]], [unit["id"]])
