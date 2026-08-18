import unittest
from unittest.mock import patch

from manhwateca.webapp.organization import naming_review_payload, serialize_naming_review


class NamingReviewPayloadTests(unittest.TestCase):
    @patch("manhwateca.webapp.organization.rename_workflow.detect_duplicates", return_value=[])
    @patch("manhwateca.webapp.organization.rename_workflow.detect_conflicts", return_value=[])
    @patch("manhwateca.webapp.organization.rename_workflow.build_plan")
    def test_groups_files_by_work(self, build_plan, _conflicts, _duplicates):
        build_plan.return_value = {
            "A": {
                "Alpha": [
                    {
                        "old_name": "Alpha_01.cbz",
                        "new_name": "Alpha - Capítulo 001.cbz",
                        "old_path": "/lib/A/Alpha/Alpha_01.cbz",
                        "new_path": "/lib/A/Alpha/Alpha - Capítulo 001.cbz",
                        "kind": "chapter",
                    },
                    {
                        "old_name": "Alpha_02.cbz",
                        "new_name": "Alpha - Capítulo 002.cbz",
                        "old_path": "/lib/A/Alpha/Alpha_02.cbz",
                        "new_path": "/lib/A/Alpha/Alpha - Capítulo 002.cbz",
                        "kind": "chapter",
                    },
                ]
            }
        }

        payload = naming_review_payload()

        self.assertEqual(payload["summary"]["suggested"], 1)
        self.assertEqual(payload["summary"]["total"], 1)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["title"], "Alpha")
        self.assertEqual(payload["items"][0]["group"], "A")
        self.assertEqual(payload["items"][0]["files_count"], 2)
        self.assertEqual(len(payload["items"][0]["changes"]), 2)
        self.assertEqual(payload["items"][0]["changes"][0]["old_name"], "Alpha_01.cbz")

    def test_blocked_work_is_separate_from_review(self):
        plan = {
            "B": {
                "Beta": [{
                    "old_name": "Beta_01.cbz",
                    "new_name": "Beta - Capítulo 001.cbz",
                    "kind": "chapter",
                }]
            }
        }
        conflicts = [{"manga": "Beta", "conflict_name": "Beta - Capítulo 001.cbz"}]
        payload = serialize_naming_review(plan, conflicts, [])

        self.assertEqual(payload["summary"]["blocked"], 1)
        self.assertEqual(payload["summary"]["review"], 0)
        self.assertEqual(payload["items"][0]["category"], "blocked")
        self.assertEqual(payload["items"][0]["blocked_count"], 1)


if __name__ == "__main__":
    unittest.main()
