import unittest

from isolation import (
    Assertion, CapabilityDeclaration, IsolationUnproven, Probe, evaluate_isolation,
)

PASSING = [Probe("network_blocked", True), Probe("filesystem_readonly", True)]
ASSERTED = [Assertion(claimed_by="--external-sandbox", mechanism="operator claim")]
DECLARED = [CapabilityDeclaration(denies_write=True, denies_terminal=True)]


class UnprovenIsolationTests(unittest.TestCase):
    def test_passing_probes_verify_isolation(self):
        record = evaluate_isolation(PASSING)

        self.assertTrue(record.verified)
        self.assertEqual(len(record.probes), 2)

    def test_an_assertion_alone_is_not_evidence(self):
        with self.assertRaises(IsolationUnproven) as ctx:
            evaluate_isolation([], assertions=ASSERTED)

        self.assertEqual(ctx.exception.reason, "no_isolation_evidence")

    def test_a_capability_declaration_alone_is_not_evidence(self):
        # The child says it denies writes and terminals. It is describing its
        # own protocol, not the operating system it runs on.
        with self.assertRaises(IsolationUnproven) as ctx:
            evaluate_isolation([], declarations=DECLARED)

        self.assertEqual(ctx.exception.reason, "no_isolation_evidence")

    def test_assertions_and_declarations_together_are_still_not_evidence(self):
        with self.assertRaises(IsolationUnproven) as ctx:
            evaluate_isolation([], assertions=ASSERTED, declarations=DECLARED)

        self.assertEqual(ctx.exception.reason, "no_isolation_evidence")
        self.assertIn("0 probes", ctx.exception.detail)

    def test_an_assertion_is_still_recorded_for_audit(self):
        record = evaluate_isolation(PASSING, assertions=ASSERTED, declarations=DECLARED)

        self.assertTrue(record.verified)
        self.assertEqual(record.assertions[0].claimed_by, "--external-sandbox")
        self.assertEqual(len(record.declarations), 1)

    def test_a_failing_probe_refuses_and_names_it(self):
        with self.assertRaises(IsolationUnproven) as ctx:
            evaluate_isolation([Probe("network_blocked", False), Probe("fs_readonly", True)])

        self.assertEqual(ctx.exception.reason, "probe_failed")
        self.assertEqual(ctx.exception.detail, "network_blocked")

    def test_an_assertion_cannot_rescue_a_failing_probe(self):
        with self.assertRaises(IsolationUnproven) as ctx:
            evaluate_isolation([Probe("network_blocked", False)], assertions=ASSERTED)

        self.assertEqual(ctx.exception.reason, "probe_failed")

    def test_the_bypass_flag_alone_does_not_work(self):
        with self.assertRaises(IsolationUnproven) as ctx:
            evaluate_isolation([], allow_unisolated=True)

        self.assertEqual(ctx.exception.reason, "bypass_not_verifiable")

    def test_the_bypass_requires_a_proof_that_actually_returns_true(self):
        with self.assertRaises(IsolationUnproven):
            evaluate_isolation([], allow_unisolated=True, local_development_proof=lambda: False)

        record = evaluate_isolation(
            [], allow_unisolated=True, local_development_proof=lambda: True
        )
        self.assertFalse(record.verified)  # allowed, and honestly unverified

    def test_a_bypassed_run_is_never_recorded_as_verified(self):
        record = evaluate_isolation(
            [], allow_unisolated=True, local_development_proof=lambda: True
        )

        self.assertFalse(record.verified)


if __name__ == "__main__":
    unittest.main()
