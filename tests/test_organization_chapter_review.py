import unittest

from manhwateca.webapp.organization import serialize_chapter_review


class ChapterReviewTest(unittest.TestCase):
    def test_gap_is_real_divergence(self):
        payload = serialize_chapter_review([{
            "nome": "Romance in Romance",
            "main_caps": 38,
            "chapters_found": 37,
            "missing_ranges": ["12"],
            "count_issues": ["lacunas"],
            "unparsed_files": [],
            "count_status": "Revisar",
        }])

        item = payload["items"][0]
        self.assertIn("Divergências", item["filters"])
        self.assertIn("Lacunas", item["filters"])
        self.assertEqual(item["gap_count"], 1)
        self.assertEqual(payload["summary"]["divergences"], 1)

    def test_duplicate_issue_is_classified(self):
        payload = serialize_chapter_review([{
            "nome": "Boredom",
            "main_caps": 10,
            "chapters_found": 10,
            "missing_ranges": [],
            "count_issues": ["sobreposições"],
            "unparsed_files": [],
            "count_status": "Revisar",
        }])

        item = payload["items"][0]
        self.assertIn("Duplicados", item["filters"])
        self.assertEqual(item["duplicate_count"], 1)

    def test_ok_sequence(self):
        payload = serialize_chapter_review([{
            "nome": "Alphega",
            "main_caps": 19,
            "chapters_found": 19,
            "missing_ranges": [],
            "count_issues": [],
            "unparsed_files": [],
            "count_status": "OK",
        }])
        self.assertEqual(payload["summary"]["divergences"], 0)
        self.assertEqual(payload["items"][0]["category"], "ok")


if __name__ == "__main__":
    unittest.main()
