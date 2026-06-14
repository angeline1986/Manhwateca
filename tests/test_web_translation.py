import unittest
from unittest.mock import AsyncMock, patch

from manhwateca.webapp.post_routes import handle_direct_post
from manhwateca.webapp.translation import translate_to_portuguese


class WebTranslationTests(unittest.TestCase):
    @patch(
        "manhwateca.webapp.translation._translate",
        new_callable=AsyncMock,
    )
    def test_translation_normalizes_text(self, translate):
        translate.return_value = "Texto traduzido."

        result = translate_to_portuguese("Text\n  to translate.")

        self.assertEqual("Texto traduzido.", result)
        translate.assert_awaited_once_with("Text to translate.")

    def test_translation_rejects_empty_text(self):
        with self.assertRaises(ValueError):
            translate_to_portuguese("")

    @patch("manhwateca.webapp.post_routes.translate_to_portuguese")
    def test_translation_route(self, translate):
        translate.return_value = "Descrição traduzida."

        payload, status = handle_direct_post(
            "/api/translate",
            {"text": "Description."},
            project_root=None,
        )

        self.assertEqual(200, status)
        self.assertEqual("Descrição traduzida.", payload["translation"])


if __name__ == "__main__":
    unittest.main()
