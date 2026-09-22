import json
import unittest

from redaction import RedactionFailure, SecretRegistry

TOKEN = "toy-token-AAAA1111"
LONGER_TOKEN = "toy-token-AAAA1111-BBBB2222"  # contains TOKEN as a prefix
KEY = b"toy-correlation-key"


class VerifiedSecretRedactionTests(unittest.TestCase):
    def setUp(self):
        self.registry = SecretRegistry([TOKEN], correlation_key=KEY)

    def test_a_secret_in_a_nested_value_is_replaced(self):
        artifact = {"run": {"auth": {"token": TOKEN}}}
        redacted = self.registry.redact(artifact)

        self.assertEqual(
            redacted["run"]["auth"]["token"], self.registry.placeholder(TOKEN)
        )
        self.assertNotIn(TOKEN, json.dumps(redacted))

    def test_a_secret_embedded_in_a_longer_string_is_replaced_in_place(self):
        line = f"GET /v1/toy Authorization: Bearer {TOKEN} -> 200"
        redacted = self.registry.redact(line)

        self.assertNotIn(TOKEN, redacted)
        self.assertTrue(redacted.startswith("GET /v1/toy Authorization: Bearer "))
        self.assertTrue(redacted.endswith(" -> 200"))

    def test_a_secret_used_as_a_dict_key_is_replaced(self):
        redacted = self.registry.redact({TOKEN: "seen in the wild"})

        self.assertIn(self.registry.placeholder(TOKEN), redacted)
        self.assertNotIn(TOKEN, redacted)

    def test_secrets_in_lists_and_bytes_are_replaced(self):
        redacted = self.registry.redact(
            {"lines": [f"used {TOKEN}"], "raw": f"raw {TOKEN}".encode("utf-8")}
        )

        self.assertNotIn(TOKEN, redacted["lines"][0])
        self.assertNotIn(TOKEN.encode("utf-8"), redacted["raw"])

    def test_the_placeholder_is_stable_so_redacted_logs_still_correlate(self):
        first = self.registry.redact(f"call 1 with {TOKEN}")
        second = self.registry.redact(f"call 2 with {TOKEN}")

        self.assertEqual(
            self.registry.placeholder(TOKEN), self.registry.placeholder(TOKEN)
        )
        self.assertEqual(first.split("with ")[1], second.split("with ")[1])

    def test_an_overlapping_secret_leaves_no_fragment_of_the_longer_one(self):
        registry = SecretRegistry([TOKEN, LONGER_TOKEN], correlation_key=KEY)
        redacted = registry.redact(f"header {LONGER_TOKEN} footer")

        self.assertNotIn(TOKEN, redacted)
        self.assertNotIn(LONGER_TOKEN, redacted)
        self.assertNotIn("-BBBB2222", redacted)  # the fragment a naive order leaves
        self.assertEqual(redacted, f"header {registry.placeholder(LONGER_TOKEN)} footer")

    def test_a_surviving_secret_is_caught_by_the_verification_pass(self):
        # Output built by something other than this redactor — the case the
        # final pass exists for.
        with self.assertRaises(RedactionFailure) as ctx:
            self.registry.assert_clean(json.dumps({"leaked": TOKEN}))

        self.assertEqual(ctx.exception.reason, "secret_survived_redaction")

    def test_the_failure_message_does_not_itself_quote_the_secret(self):
        with self.assertRaises(RedactionFailure) as ctx:
            self.registry.assert_clean(f"oops {TOKEN}")

        self.assertNotIn(TOKEN, str(ctx.exception))
        self.assertIn(self.registry.placeholder(TOKEN), str(ctx.exception))

    def test_emit_returns_canonical_json_with_no_secret_in_it(self):
        emitted = self.registry.emit({"b": TOKEN, "a": [TOKEN, 1, None, True]})

        self.assertNotIn(TOKEN, emitted)
        self.assertEqual(emitted, json.dumps(json.loads(emitted), sort_keys=True,
                                             separators=(",", ":")))

    def test_non_string_leaves_pass_through_unchanged(self):
        payload = {"count": 3, "ratio": 0.5, "ok": True, "missing": None}
        self.assertEqual(self.registry.redact(payload), payload)

    def test_a_too_short_secret_is_rejected_at_registration(self):
        with self.assertRaises(RedactionFailure) as ctx:
            SecretRegistry(["ab"], correlation_key=KEY)
        self.assertEqual(ctx.exception.reason, "invalid_secret")

    def test_an_empty_correlation_key_is_rejected(self):
        with self.assertRaises(RedactionFailure) as ctx:
            SecretRegistry([TOKEN], correlation_key=b"")
        self.assertEqual(ctx.exception.reason, "invalid_correlation_key")


if __name__ == "__main__":
    unittest.main()
