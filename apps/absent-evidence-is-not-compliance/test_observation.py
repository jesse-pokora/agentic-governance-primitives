import unittest

from observation import ObservationRejected, RunLedger, merge

DECLARED = ("RS-001", "RS-002", "RS-003")


class AbsentEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.ledger = RunLedger(declared=DECLARED)

    def test_an_unobserved_criterion_appears_as_not_observed(self):
        self.ledger.record("RS-001", "passed", "fixture accepted")

        statuses = {row.criterion_id: row.status for row in self.ledger.report()}
        self.assertEqual(statuses["RS-001"], "passed")
        self.assertEqual(statuses["RS-002"], "not_observed")
        self.assertEqual(statuses["RS-003"], "not_observed")

    def test_an_unobserved_criterion_is_never_dropped_from_the_report(self):
        self.ledger.record("RS-001", "passed", "fixture accepted")

        self.assertEqual(len(self.ledger.report()), len(DECLARED))

    def test_nothing_failed_is_not_the_same_as_a_clean_run(self):
        self.ledger.record("RS-001", "passed", "fixture accepted")

        self.assertFalse(any(r.status == "failed" for r in self.ledger.report()))
        self.assertFalse(self.ledger.clean())
        self.assertEqual(self.ledger.observed(), (1, 3))

    def test_a_run_that_observed_everything_and_passed_is_clean(self):
        for criterion in DECLARED:
            self.ledger.record(criterion, "passed", "fixture accepted")

        self.assertTrue(self.ledger.clean())
        self.assertEqual(self.ledger.observed(), (3, 3))

    def test_one_failure_is_not_clean(self):
        self.ledger.record("RS-001", "passed", "fixture accepted")
        self.ledger.record("RS-002", "failed", "fixture rejected at line 4")
        self.ledger.record("RS-003", "passed", "fixture accepted")

        self.assertFalse(self.ledger.clean())

    def test_an_observation_without_evidence_is_refused(self):
        for blank in ("", "   ", "\n"):
            with self.subTest(evidence=blank):
                with self.assertRaises(ObservationRejected) as ctx:
                    RunLedger(declared=DECLARED).record("RS-001", "passed", blank)
                self.assertEqual(ctx.exception.reason, "evidence_required")

    def test_not_observed_cannot_be_recorded_deliberately(self):
        # It is the absence of a record. Letting a run write it would let a
        # criterion be marked unlooked-at on purpose, which is worse than the
        # gap it describes.
        with self.assertRaises(ObservationRejected) as ctx:
            self.ledger.record("RS-001", "not_observed", "skipped")

        self.assertEqual(ctx.exception.reason, "cannot_record_not_observed")

    def test_an_undeclared_criterion_is_refused(self):
        with self.assertRaises(ObservationRejected) as ctx:
            self.ledger.record("RS-999", "passed", "evidence")

        self.assertEqual(ctx.exception.reason, "undeclared_criterion")

    def test_observing_the_same_criterion_twice_is_refused(self):
        self.ledger.record("RS-001", "passed", "fixture accepted")

        with self.assertRaises(ObservationRejected) as ctx:
            self.ledger.record("RS-001", "failed", "fixture rejected")

        self.assertEqual(ctx.exception.reason, "already_observed")

    def test_merging_runs_accumulates_coverage(self):
        first = RunLedger(declared=DECLARED)
        first.record("RS-001", "passed", "run 1")
        second = RunLedger(declared=DECLARED)
        second.record("RS-002", "passed", "run 2")

        combined = merge(first, second)

        self.assertEqual(combined.observed(), (2, 3))
        self.assertFalse(combined.clean())

    def test_merging_runs_that_disagree_is_refused(self):
        first = RunLedger(declared=DECLARED)
        first.record("RS-001", "passed", "run 1")
        second = RunLedger(declared=DECLARED)
        second.record("RS-001", "failed", "run 2")

        with self.assertRaises(ObservationRejected) as ctx:
            merge(first, second)

        self.assertEqual(ctx.exception.reason, "conflicting_observations")

    def test_merging_different_declarations_is_refused(self):
        with self.assertRaises(ObservationRejected) as ctx:
            merge(RunLedger(declared=DECLARED), RunLedger(declared=("RS-001",)))

        self.assertEqual(ctx.exception.reason, "declaration_mismatch")


if __name__ == "__main__":
    unittest.main()
