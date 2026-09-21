import unittest

from review_loop import BoundedReviewEpoch, EscalationRequired, ReauthorizationDenied


class BoundedReviewEpochTests(unittest.TestCase):
    def test_closes_before_cap_when_findings_resolve(self):
        epoch = BoundedReviewEpoch(max_rounds_per_epoch=3)
        r1 = epoch.submit_round(["missing null check"])
        self.assertEqual(r1.status, "continue")
        r2 = epoch.submit_round([])
        self.assertEqual(r2.status, "closed")

    def test_escalates_after_cap_with_findings_still_open(self):
        epoch = BoundedReviewEpoch(max_rounds_per_epoch=3)
        epoch.submit_round(["finding A"])
        epoch.submit_round(["finding A"])
        r3 = epoch.submit_round(["finding A"])

        self.assertEqual(r3.status, "escalation_required")
        self.assertIsNotNone(r3.terminal_evidence_hash)

    def test_loop_cannot_self_extend_past_the_cap(self):
        epoch = BoundedReviewEpoch(max_rounds_per_epoch=3)
        epoch.submit_round(["finding A"])
        epoch.submit_round(["finding A"])
        epoch.submit_round(["finding A"])

        with self.assertRaises(EscalationRequired):
            epoch.submit_round(["finding A"])

    def test_reauthorization_with_wrong_hash_is_denied(self):
        epoch = BoundedReviewEpoch(max_rounds_per_epoch=3)
        epoch.submit_round(["finding A"])
        epoch.submit_round(["finding A"])
        epoch.submit_round(["finding A"])

        with self.assertRaises(ReauthorizationDenied) as ctx:
            epoch.reauthorize("0" * 64)
        self.assertEqual(ctx.exception.reason, "evidence_hash_mismatch")

    def test_correct_reauthorization_unlocks_exactly_one_more_epoch(self):
        epoch = BoundedReviewEpoch(max_rounds_per_epoch=3)
        epoch.submit_round(["finding A"])
        epoch.submit_round(["finding A"])
        escalation = epoch.submit_round(["finding A"])

        epoch.reauthorize(escalation.terminal_evidence_hash)

        r4 = epoch.submit_round(["finding A"])
        self.assertEqual(r4.status, "continue")

    def test_new_epoch_re_escalates_with_a_fresh_hash_not_the_old_one(self):
        epoch = BoundedReviewEpoch(max_rounds_per_epoch=3)
        epoch.submit_round(["finding A"])
        epoch.submit_round(["finding A"])
        first_escalation = epoch.submit_round(["finding A"])
        epoch.reauthorize(first_escalation.terminal_evidence_hash)

        epoch.submit_round(["finding A"])
        epoch.submit_round(["finding A"])
        second_escalation = epoch.submit_round(["finding A"])

        self.assertEqual(second_escalation.status, "escalation_required")
        self.assertNotEqual(
            second_escalation.terminal_evidence_hash,
            first_escalation.terminal_evidence_hash,
        )
        # The old hash must not authorize the new escalation.
        with self.assertRaises(ReauthorizationDenied):
            epoch.reauthorize(first_escalation.terminal_evidence_hash)


if __name__ == "__main__":
    unittest.main()
