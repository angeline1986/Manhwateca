import unittest
from pathlib import Path

from manhwateca.webapp.organization import serialize_folder_organization


class FolderOrganizationReviewTest(unittest.TestCase):
    def test_move_is_grouped_by_work(self):
        root = Path("/library")
        plan = [{
            "name": "Boredom",
            "source": root / "Downloads" / "Boredom",
            "destination": root / "B" / "Boredom",
            "group": "B",
            "current_group": "Downloads",
            "is_correct": False,
            "total_caps": 1,
        }]

        payload = serialize_folder_organization(plan, [], [], root)

        self.assertEqual(payload["summary"]["move"], 1)
        self.assertEqual(payload["items"][0]["title"], "Boredom")
        self.assertEqual(payload["items"][0]["category"], "move")
        self.assertTrue(payload["items"][0]["destination"].endswith("B/Boredom"))

    def test_correct_folder_is_keep(self):
        root = Path("/library")
        path = root / "A" / "Alphega"
        plan = [{
            "name": "Alphega",
            "source": path,
            "destination": path,
            "group": "A",
            "current_group": "A",
            "is_correct": True,
            "total_caps": 19,
        }]

        payload = serialize_folder_organization(plan, [], [], root)

        self.assertEqual(payload["summary"]["keep"], 1)
        self.assertEqual(payload["items"][0]["category"], "keep")


if __name__ == "__main__":
    unittest.main()
