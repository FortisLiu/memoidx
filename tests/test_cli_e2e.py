import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliEndToEndTests(unittest.TestCase):
    def test_initialize_add_search_recall_forget(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            config = base / "config.json"
            config.write_text(json.dumps({"user_root": "user/.memoidx", "project_root": "project/.memoidx"}))
            def run(*args):
                process = subprocess.run([sys.executable, "-m", "memoidx", "--json", "--config", str(config), *args], capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
                return json.loads(process.stdout)
            run("init", "--scope", "project")
            request = base / "add.json"
            request.write_text(json.dumps(dict(request_id="cli-add", file="answers.md", content="preference", retention="pinned", source="user")))
            added = run("edit", "add", "--input", str(request))
            self.assertEqual(run("edit", "add", "--input", str(request)), added)
            self.assertEqual(run("search", "preference")[0]["id"], added["id"])
            self.assertEqual(run("recall", "--id", added["id"])["content"], "preference")
            run("forget", "--id", added["id"])
            self.assertEqual(run("search", "preference"), [])
