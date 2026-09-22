import unittest

from grounding import Claim, GroundTruth, GroundingRejected, verify_claims

GROUND_TRUTH = GroundTruth(
    {
        "svc-fake-a.owner": "toy-team-alpha",
        "svc-fake-a.replicas": "4",
        "svc-fake-b.owner": "toy-team-beta",
    }
)


class GroundedClaimVerificationTests(unittest.TestCase):
    def test_fully_grounded_claims_pass(self):
        claims = [
            Claim("svc-fake-a is owned by toy-team-alpha", "svc-fake-a.owner", "toy-team-alpha"),
            Claim("svc-fake-a runs 4 replicas", "svc-fake-a.replicas", "4"),
        ]
        verify_claims(claims, GROUND_TRUTH)  # raises on failure

    def test_an_uncited_claim_is_rejected(self):
        claims = [Claim("svc-fake-a is probably fine", None, None)]

        with self.assertRaises(GroundingRejected) as ctx:
            verify_claims(claims, GROUND_TRUTH)

        self.assertEqual(ctx.exception.reason, "uncited_claim")
        self.assertEqual(ctx.exception.claim_index, 0)

    def test_a_fabricated_source_key_is_rejected(self):
        # The most convincing drift: it looks cited.
        claims = [Claim("svc-fake-c is owned by toy-team-gamma", "svc-fake-c.owner", "toy-team-gamma")]

        with self.assertRaises(GroundingRejected) as ctx:
            verify_claims(claims, GROUND_TRUTH)

        self.assertEqual(ctx.exception.reason, "unknown_source")
        self.assertEqual(ctx.exception.detail, "svc-fake-c.owner")

    def test_an_altered_quote_against_a_real_key_is_rejected(self):
        # Right key, drifted value — the failure a citation check alone misses.
        claims = [Claim("svc-fake-a runs 8 replicas", "svc-fake-a.replicas", "8")]

        with self.assertRaises(GroundingRejected) as ctx:
            verify_claims(claims, GROUND_TRUTH)

        self.assertEqual(ctx.exception.reason, "quote_mismatch")
        self.assertIn("quoted='8'", ctx.exception.detail)
        self.assertIn("actual='4'", ctx.exception.detail)

    def test_a_near_miss_quote_is_still_a_mismatch(self):
        for drifted in ("toy-team-Alpha", "toy-team-alpha ", "toy team alpha"):
            with self.subTest(quoted=drifted):
                with self.assertRaises(GroundingRejected) as ctx:
                    verify_claims(
                        [Claim("owner", "svc-fake-a.owner", drifted)], GROUND_TRUTH
                    )
                self.assertEqual(ctx.exception.reason, "quote_mismatch")

    def test_a_missing_quote_on_a_real_key_is_rejected(self):
        claims = [Claim("svc-fake-a has an owner", "svc-fake-a.owner", None)]

        with self.assertRaises(GroundingRejected) as ctx:
            verify_claims(claims, GROUND_TRUTH)

        self.assertEqual(ctx.exception.reason, "quote_mismatch")

    def test_the_first_bad_claim_is_the_one_reported(self):
        claims = [
            Claim("svc-fake-a is owned by toy-team-alpha", "svc-fake-a.owner", "toy-team-alpha"),
            Claim("invented", "svc-fake-z.owner", "nobody"),
            Claim("also uncited", None, None),
        ]

        with self.assertRaises(GroundingRejected) as ctx:
            verify_claims(claims, GROUND_TRUTH)

        self.assertEqual(ctx.exception.reason, "unknown_source")
        self.assertEqual(ctx.exception.claim_index, 1)

    def test_an_output_with_no_claims_passes_vacuously(self):
        # Worth stating explicitly: this gate constrains the claims that are
        # made, not whether any are made. "Say nothing" is always grounded.
        verify_claims([], GROUND_TRUTH)


if __name__ == "__main__":
    unittest.main()
