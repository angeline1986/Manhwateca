import unittest
import unicodedata
from pathlib import Path
from tempfile import TemporaryDirectory

from manhwateca.library_organizer.planning import build_plan
from manhwateca.webapp.organization import serialize_structure_review


class OrganizationStructureReviewTests(unittest.TestCase):
    def test_unicode_equivalent_path_is_correct_without_changing_source(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            nfc_name = "Armadilha de Açucar"
            nfd_name = unicodedata.normalize("NFD", nfc_name)
            source = root / "A" / nfd_name
            source.mkdir(parents=True)

            plan = build_plan(
                [source],
                root,
                lambda _name: "A",
                lambda _path: "A",
            )

            self.assertTrue(plan[0]["is_correct"])
            self.assertEqual(plan[0]["source"], source)
            self.assertEqual(plan[0]["destination"], root / "A" / nfc_name)
            self.assertNotEqual(str(plan[0]["source"]), str(plan[0]["destination"]))

            payload = serialize_structure_review(plan, [], [], root)

            self.assertEqual(payload["summary"]["ok"], 1)
            self.assertEqual(payload["items"][0]["category"], "ok")

    def test_really_different_path_stays_divergence(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "A princesa bebe2"
            source.mkdir()

            plan = build_plan(
                [source],
                root,
                lambda _name: "A",
                lambda _path: "library",
            )

            self.assertFalse(plan[0]["is_correct"])

            payload = serialize_structure_review(plan, [], [], root)

            self.assertEqual(payload["summary"]["divergences"], 1)
            self.assertEqual(payload["items"][0]["category"], "divergence")

    def test_ascii_path_still_matches_normally(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "ST" / "To You At Dawn"
            source.mkdir(parents=True)

            plan = build_plan(
                [source],
                root,
                lambda _name: "ST",
                lambda _path: "ST",
            )

            self.assertTrue(plan[0]["is_correct"])

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
        self.assertEqual(payload["items"][0]["category"], "duplicate")

    def test_move_without_conflict_is_divergence_for_structure_review(self):
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

        self.assertEqual(payload["summary"]["ok"], 0)
        self.assertEqual(payload["summary"]["divergences"], 1)
        self.assertTrue(payload["items"][0]["movement_required"])
        self.assertEqual(payload["items"][0]["category"], "divergence")
        self.assertEqual(payload["items"][0]["status"], "Será movido")
        self.assertEqual(
            payload["items"][0]["issue_description"],
            "A obra está fora da pasta/grupo esperado. Revise a movimentação "
            "em Organizar pastas.",
        )

    def test_movement_required_item_is_never_ok(self):
        root = Path("/library")
        item = {
            "name": "To You At Dawn",
            "source": root / "To You At Dawn",
            "destination": root / "ST" / "To You At Dawn",
            "group": "ST",
            "current_group": "library",
            "exists": False,
            "is_correct": False,
            "main_caps": 4,
            "side_caps": 0,
            "total_caps": 4,
        }

        payload = serialize_structure_review([item], [], [], root)

        self.assertTrue(payload["items"][0]["movement_required"])
        self.assertNotEqual(payload["items"][0]["category"], "ok")

    def test_conflict_is_classified_as_divergence(self):
        root = Path("/library")
        item = {
            "name": "Blocked Move",
            "source": root / "B" / "Blocked Move",
            "destination": root / "BC" / "Blocked Move",
            "group": "BC",
            "current_group": "B",
            "exists": True,
            "is_correct": False,
            "main_caps": 3,
            "side_caps": 0,
            "total_caps": 3,
        }
        conflict = {
            "destination": str(item["destination"]),
            "items": [item],
            "reason": "destino_existente",
        }

        payload = serialize_structure_review([item], [conflict], [], root)

        self.assertEqual(payload["summary"]["divergences"], 1)
        self.assertEqual(payload["items"][0]["category"], "divergence")
        self.assertEqual(payload["items"][0]["status"], "Conflito")

    def test_correct_folder_text_mentions_expected_folder_and_group(self):
        root = Path("/library")
        item = {
            "name": "A Agenda Alfa",
            "source": root / "A" / "A Agenda Alfa",
            "destination": root / "A" / "A Agenda Alfa",
            "group": "A",
            "current_group": "A",
            "exists": True,
            "is_correct": True,
            "main_caps": 5,
            "side_caps": 0,
            "total_caps": 5,
        }

        payload = serialize_structure_review([item], [], [], root)

        self.assertEqual(payload["summary"]["ok"], 1)
        self.assertEqual(payload["items"][0]["category"], "ok")
        self.assertEqual(
            payload["items"][0]["issue_description"],
            "A obra já está na pasta e no grupo esperados.",
        )


if __name__ == "__main__":
    unittest.main()
