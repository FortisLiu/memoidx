import tempfile
import unittest
from pathlib import Path
from memoidx.init import initialize
from memoidx.edit import add_memory, show_memory, update_memory
from memoidx.search import search
from memoidx.explain import explain
from memoidx.forget import forget


class ExplainTests(unittest.TestCase):
    def test_search_versions_and_forget_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = initialize(Path(directory))
            result = add_memory(root, dict(request_id="one", file="a.md", content="alpha beta", source="user", retention="pinned"))
            first = search({"project": root}, "alpha")[0]
            second = search({"project": root}, "beta")[0]
            self.assertNotEqual(first["search_id"], second["search_id"])
            self.assertEqual(explain(root, first["search_id"], result["id"])["body_hits"], ["alpha"])
            unit = show_memory(root, result["id"])
            request = dict(request_id="update-one", id=result["id"], expected_revision=unit["revision"], content="gamma")
            updated = update_memory(root, request)
            self.assertEqual(update_memory(root, request), updated)
            self.assertTrue(explain(root, first["search_id"], result["id"])["historical"])
            forget(root, result["id"])
            self.assertFalse(list((root / "_state" / "searches").glob("*.json")))
