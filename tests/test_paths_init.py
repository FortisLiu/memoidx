import json
import tempfile
import unittest
from pathlib import Path

from memoidx.init import initialize
from memoidx.paths import PathConfigError, ensure_inside, load_roots


class PathsInitTests(unittest.TestCase):
    def test_config_paths_are_relative_to_config_and_init_is_idempotent(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            config = root / "config.json"
            config.write_text(json.dumps({"user_root": "user/.memoidx", "project_root": "project"}), encoding="utf-8")
            user, project = load_roots(config)
            initialize(project)
            marker = project / "marker.txt"
            marker.write_text("keep", encoding="utf-8")
            initialize(project)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")
            self.assertTrue((project / "_state" / "trash").is_dir())
            self.assertEqual(user, (root / "user/.memoidx").resolve())

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            with self.assertRaises(PathConfigError):
                ensure_inside(directory, "../../outside.md")


if __name__ == "__main__":
    unittest.main()
