import tempfile
import unittest
from pathlib import Path

from manhwateca.webapp.reviews import save_review_note


class WebReviewTests(unittest.TestCase):
    def test_review_note_uses_shared_review_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            saved = save_review_note(root, "Corrigir capa duplicada")
            path = root / "reports/reviews/review_notes.md"

            self.assertTrue(saved)
            self.assertIn(
                "- [ ] Corrigir capa duplicada",
                path.read_text(encoding="utf-8"),
            )
