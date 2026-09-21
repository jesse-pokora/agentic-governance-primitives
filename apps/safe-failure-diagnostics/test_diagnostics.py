import json
import unittest

from diagnostics import (
    MAX_INSPECTED_BYTES,
    classify_failure,
    persist_failure,
)


class SafeFailureDiagnosticsTests(unittest.TestCase):
    def test_classifies_permission_denied(self):
        self.assertEqual(
            classify_failure(b"bash: /opt/toy: Permission denied"),
            "permission_denied",
        )

    def test_classifies_not_found(self):
        self.assertEqual(
            classify_failure(b"sh: toy-cmd: No such file or directory"),
            "not_found",
        )

    def test_classifies_crash(self):
        self.assertEqual(
            classify_failure(b"Segmentation fault (core dumped)"),
            "crash",
        )

    def test_unrecognized_output_is_unknown(self):
        self.assertEqual(classify_failure(b"toy-tool: exit code 3"), "unknown")

    def test_persisted_record_contains_only_the_category_field(self):
        record = persist_failure(b"bash: /home/jp22662/secret.key: Permission denied")
        self.assertEqual(set(record.keys()), {"category"})
        self.assertEqual(record["category"], "permission_denied")

    def test_persisted_record_never_contains_raw_bytes(self):
        raw = b"leaked-secret-token-XYZ: Permission denied"
        record = persist_failure(raw)
        serialized = json.dumps(record)
        self.assertNotIn("leaked-secret-token-XYZ", serialized)

    def test_only_the_first_max_inspected_bytes_are_considered(self):
        # The marker sits just past the inspection boundary, so it must not
        # be found — proving the classifier never reads past the bound.
        padding = b"x" * MAX_INSPECTED_BYTES
        raw = padding + b"Segmentation fault"
        self.assertEqual(classify_failure(raw), "unknown")


if __name__ == "__main__":
    unittest.main()
