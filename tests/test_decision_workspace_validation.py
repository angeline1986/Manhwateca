import unittest
from types import SimpleNamespace

from manhwateca.webapp.mangaupdates_decisions import validate_decisions_payload


class DecisionWorkspaceValidationTests(unittest.TestCase):
    def test_catalog_ownership_blocks_other_work(self):
        class Repository:
            def find_by_id(self, work_id):
                return SimpleNamespace(id=work_id, title="Guiding Hazard")

            def find_by_work_code(self, work_code):
                if work_code == "57517288552":
                    return SimpleNamespace(id=7, title="Perigo Orientador")
                return None

        decision = {"queueId": "flow_42", "Nome": "Guiding Hazard", "ID": 57517288552}
        payload = validate_decisions_payload([decision], Repository())

        self.assertFalse(payload["valid"])
        self.assertEqual(1, payload["blocked"])
        self.assertIn("Perigo Orientador", payload["blocks"][0]["reason"])

    def test_duplicate_id_in_batch_is_blocked(self):
        payload = validate_decisions_payload([
            {"Nome": "Alpha", "ID": 123},
            {"Nome": "Beta", "ID": 123},
        ])

        self.assertFalse(payload["valid"])
        self.assertIn("Alpha", payload["blocks"][0]["reason"])

    def test_same_work_can_keep_its_id(self):
        class Repository:
            def find_by_id(self, work_id):
                return SimpleNamespace(id=work_id, title="Alpha")

            def find_by_work_code(self, _work_code):
                return SimpleNamespace(id=42, title="Alpha")

        payload = validate_decisions_payload([
            {"queueId": "flow_42", "Nome": "Alpha", "ID": 123},
        ], Repository())

        self.assertTrue(payload["valid"])


if __name__ == "__main__":
    unittest.main()
