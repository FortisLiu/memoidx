import tempfile
import unittest
from memoidx.init import initialize
from memoidx.edit import add_memory, show_memory, update_memory
from memoidx.maintenance import read, apply
from memoidx.folders import read_folder, apply_folder
from memoidx.search import search


class FolderTests(unittest.TestCase):
    def test_fresh_folder_scoring_and_stale_invalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = initialize(directory)
            added = add_memory(root, dict(request_id="folder", file="a.md", content="body", retention="pinned", source="user"))
            source = read(root, "a.md")
            apply(root, "a.md", source["source_hash"], ["file", "summary", "keywords"])
            folder = read_folder(root, ".")
            apply_folder(root, ".", folder["source_hash"], ["folderword", "scope", "keywords"])
            found = search({"project": root}, "folderword")
            self.assertEqual(found[0]["score"], 1)
            self.assertEqual(found[0]["id"], added["id"])
            unit = show_memory(root, added["id"])
            update_memory(root, dict(id=unit["id"], expected_revision=unit["revision"], content="changed"))
            self.assertEqual(search({"project": root}, "folderword"), [])
            with self.assertRaisesRegex(ValueError, "REVISION_CONFLICT"):
                apply_folder(root, ".", folder["source_hash"], ["old", "old", "old"])
