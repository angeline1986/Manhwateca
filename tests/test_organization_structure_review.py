import unittest
from pathlib import Path

from manhwateca.webapp.organization import serialize_structure_review


class OrganizationStructureReviewTests(unittest.TestCase):
    def test_duplicate_is_classified_as_duplicate(self):
        root = Path("/library")
        a = {
            "name": "Romance in Romance",
            "source": root / "R" / "Romance in Romance",
            "destination": root / "PQR" / "Romance in Romance",
            "group": "PQR",
            "current_group": "R",
            "exists": False,
            "is_correct": False,
            "main_caps": 10,
            "side_caps": 0,
            "total_caps": 10,
        }
        b = {
            **a,
            "source": root / "R" / "Romance in Romance 2",
            "main_caps": 8,
            "total_caps": 8,
        }
        duplicate = {
            "normalized": "romance in romance",
            "entries": [
                {
                    "original": a["name"],
                    "source": str(a["source"]),
                    "destination": str(a["destination"]),
                    "group": a["group"],
                },
                {
                    "original": b["name"],
                    "source": str(b["source"]),
                    "destination": str(b["destination"]),
                    "group": b["group"],
                },
            ],
        }

        payload = serialize_structure_review([a, b], [], [duplicate], root)

        self.assertEqual(payload["summary"]["duplicates"], 1)
        self.assertEqual(payload["summary"]["divergences"], 0)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["current_structure"], "2 pastas")
        self.assertEqual(payload["items"][0]["files"], 18)

    def test_move_without_conflict_is_ok_for_structure_review(self):
        root = Path("/library")
        item = {
            "name": "Alphega",
            "source": root / "Outros" / "Alphega",
            "destination": root / "A" / "Alphega",
            "group": "A",
            "current_group": "Outros",
            "exists": False,
            "is_correct": False,
            "main_caps": 19,
            "side_caps": 0,
            "total_caps": 19,
        }

        payload = serialize_structure_review([item], [], [], root)

        self.assertEqual(payload["summary"]["ok"], 1)
        self.assertEqual(payload["summary"]["divergences"], 0)
        self.assertTrue(payload["items"][0]["movement_required"])
        self.assertEqual(payload["items"][0]["category"], "ok")


if __name__ == "__main__":
    unittest.main()
