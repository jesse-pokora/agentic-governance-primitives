import json
import unittest

from preflight import ALLOWED_FIELDS, run_preflight


class GovernedPreflightDenialEvidenceTests(unittest.TestCase):
    def test_passing_precondition_returns_no_record(self):
        record = run_preflight("disk_space_check", lambda: None)
        self.assertIsNone(record)

    def test_failing_precondition_returns_fixed_shape_record(self):
        record = run_preflight("disk_space_check", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        self.assertIsNotNone(record)
        self.assertEqual(set(record.to_dict().keys()), ALLOWED_FIELDS)

    def test_denial_record_never_leaks_secrets_or_paths_from_the_exception(self):
        secret = "sk_live_supersecrettoken12345"
        path = "/home/jp22662/.ssh/id_rsa"

        def failing_check():
            raise RuntimeError(f"connection failed using key at {path} with token {secret}")

        record = run_preflight("credential_check", failing_check)
        serialized = json.dumps(record.to_dict())

        self.assertNotIn(secret, serialized)
        self.assertNotIn(path, serialized)
        self.assertNotIn("id_rsa", serialized)

    def test_denial_record_uses_fixed_reason_code_regardless_of_exception_type(self):
        record_a = run_preflight("check_a", lambda: (_ for _ in ()).throw(ValueError("x")))
        record_b = run_preflight("check_b", lambda: (_ for _ in ()).throw(OSError("y")))

        self.assertEqual(record_a.reason_code, record_b.reason_code)


if __name__ == "__main__":
    unittest.main()
