import unittest

from manhwateca.audit.sanitizer import MASK, sanitize_audit_details


class AuditSanitizerTests(unittest.TestCase):
    def test_masks_root_token(self):
        self.assertEqual(
            {"token": MASK},
            sanitize_audit_details({"token": "abc"}),
        )

    def test_masks_password(self):
        self.assertEqual(
            {"password": MASK},
            sanitize_audit_details({"password": "secret"}),
        )

    def test_masks_database_url(self):
        self.assertEqual(
            {"DATABASE_URL": MASK},
            sanitize_audit_details({"DATABASE_URL": "postgres://secret"}),
        )

    def test_masks_nested_values(self):
        value = {"config": {"notion": {"token": "abc"}}}

        self.assertEqual(
            {"config": {"notion": {"token": MASK}}},
            sanitize_audit_details(value),
        )

    def test_masks_values_inside_list(self):
        value = {"items": [{"api_key": "abc"}, {"name": "ok"}]}

        self.assertEqual(
            {"items": [{"api_key": MASK}, {"name": "ok"}]},
            sanitize_audit_details(value),
        )

    def test_preserves_non_sensitive_fields(self):
        value = {"module": "flows", "count": 2, "enabled": True}

        self.assertEqual(value, sanitize_audit_details(value))

    def test_converts_non_json_objects_to_string(self):
        class CustomObject:
            def __str__(self):
                return "custom"

        self.assertEqual("custom", sanitize_audit_details(CustomObject()))


if __name__ == "__main__":
    unittest.main()
