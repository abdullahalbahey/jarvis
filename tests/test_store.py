import os
import tempfile
import unittest
from unittest.mock import patch


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.env = patch.dict(os.environ, {"DATABASE_PATH": self.tmp.name})
        self.env.start()
        import store
        self.store = store
        self.store.DB_PATH = self.tmp.name
        self.store.init_db()

    def tearDown(self):
        self.env.stop()
        try:
            os.unlink(self.tmp.name)
        except FileNotFoundError:
            pass

    def test_note_round_trip(self):
        note_id = self.store.add_note("personal", "My insight", "Requirements need context.")
        note = self.store.recent_notes()[0]
        self.assertEqual(note["id"], note_id)
        self.assertEqual(note["body"], "Requirements need context.")
        self.assertEqual(note["sources"], [])

    def test_draft_review(self):
        draft_id = self.store.add_draft("AI and BA", "Draft text", [{"title": "Source", "url": "https://example.com"}])
        self.assertEqual(self.store.get_draft(draft_id)["status"], "draft")
        self.assertTrue(self.store.set_draft_status(draft_id, "approved"))
        self.assertEqual(self.store.get_draft(draft_id)["status"], "approved")
        self.assertFalse(self.store.set_draft_status(999999, "rejected"))

    def test_invalid_status(self):
        with self.assertRaises(ValueError):
            self.store.set_draft_status(1, "published")


if __name__ == "__main__":
    unittest.main()
