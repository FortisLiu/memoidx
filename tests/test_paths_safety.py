import json
import tempfile
import unittest
from pathlib import Path
from memoidx.paths import load_roots, find_project_root, ensure_inside, PathConfigError
from memoidx.init import initialize
from memoidx.edit import add_memory


class PathSafetyTests(unittest.TestCase):
    def test_project_config_appends_memory_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "settings.json"
            config.write_text(json.dumps({"user_root": "user/.memoidx", "project_root": "project"}))
            user, project = load_roots(config)
            self.assertEqual(project, root / "project" / ".memoidx")
            initialize(project)
            nested = root / "project" / "nested" / "child"
            nested.mkdir(parents=True)
            self.assertEqual(find_project_root(nested), project)

    def test_internal_files_cannot_be_used_as_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = initialize(directory)
            for path in ("README.md", "_state/injected.md", "../outside.md"):
                with self.subTest(path=path):
                    with self.assertRaises(ValueError):
                        add_memory(root, dict(request_id=path, file=path, content="x", retention="normal", source="user"))

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "real").mkdir()
            try:
                (root / "link").symlink_to(root / "real", target_is_directory=True)
            except OSError:
                self.skipTest("symlink creation unavailable on this Windows account")
            with self.assertRaises(PathConfigError):
                ensure_inside(root, "link/card.md")
