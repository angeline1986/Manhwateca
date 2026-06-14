import unittest
from unittest.mock import patch

from manhwateca.webapp.mangaupdates_search import search_payload
from manhwateca.webapp.post_routes import handle_direct_post


class WebMangaUpdatesSearchTests(unittest.TestCase):
    @patch("manhwateca.webapp.mangaupdates_search.search_series")
    def test_search_returns_requested_fields_and_five_sentences(self, search):
        search.return_value = {"results": [{"record": {
            "series_id": 123,
            "title": "Flip the Script",
            "url": "https://example.test/flip",
            "description": "One. Two! Three? Four. Five. Six.",
        }}]}

        payload = search_payload("Flip the Script")

        self.assertEqual([{
            "series_id": 123,
            "title": "Flip the Script",
            "url": "https://example.test/flip",
            "description": "One. Two! Three? Four. Five.",
        }], payload["results"])

    def test_search_requires_two_characters(self):
        with self.assertRaises(ValueError):
            search_payload("A")

    @patch("manhwateca.webapp.post_routes.search_payload")
    def test_post_route_maps_mangaupdates_search(self, search):
        search.return_value = {"query": "Alpha", "results": []}

        payload, status = handle_direct_post(
            "/api/mangaupdates/search",
            {"query": "Alpha"},
            project_root=None,
        )

        self.assertEqual(200, status)
        self.assertEqual("Alpha", payload["query"])
        search.assert_called_once_with("Alpha")


if __name__ == "__main__":
    unittest.main()
