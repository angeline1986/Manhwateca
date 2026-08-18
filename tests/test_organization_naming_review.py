import unittest
from unittest.mock import patch

from manhwateca.webapp.organization import naming_review_payload


class NamingReviewPayloadTests(unittest.TestCase):
    @patch('manhwateca.webapp.organization.rename_workflow.detect_duplicates', return_value=[])
    @patch('manhwateca.webapp.organization.rename_workflow.detect_conflicts', return_value=[])
    @patch('manhwateca.webapp.organization.rename_workflow.build_plan')
    def test_serializes_real_rename_plan(self, build_plan, _conflicts, _duplicates):
        build_plan.return_value = {
            'A': {'Alpha': [{
                'old_name': 'Alpha_01.cbz',
                'new_name': 'Alpha - Capítulo 001.cbz',
                'old_path': '/lib/A/Alpha/Alpha_01.cbz',
                'new_path': '/lib/A/Alpha/Alpha - Capítulo 001.cbz',
                'kind': 'chapter',
            }]}
        }
        payload = naming_review_payload()
        self.assertEqual(payload['summary']['suggested'], 1)
        self.assertEqual(payload['items'][0]['group'], 'A')
        self.assertEqual(payload['items'][0]['old_name'], 'Alpha_01.cbz')
        self.assertEqual(payload['items'][0]['new_name'], 'Alpha - Capítulo 001.cbz')


if __name__ == '__main__':
    unittest.main()
