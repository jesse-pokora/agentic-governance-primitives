import unittest

from escalation_gate import NoTierPassed, Tier, TieredEscalationGate


class SpyTier:
    """Records how many times this tier was actually called."""

    def __init__(self, result, raises=False):
        self.calls = 0
        self.result = result
        self.raises = raises

    def __call__(self, prompt):
        self.calls += 1
        if self.raises:
            raise RuntimeError("toy tier failure")
        return self.result


def is_grounded(output):
    """The declared check: output must cite a source. Deterministic."""
    return isinstance(output, dict) and bool(output.get("source_key"))


GOOD = {"text": "svc-fake-a is owned by toy-team-alpha", "source_key": "svc-fake-a.owner"}
UNGROUNDED = {"text": "svc-fake-a is probably fine", "source_key": None}


class TieredModelEscalationGateTests(unittest.TestCase):
    def test_a_passing_cheap_tier_answers_and_the_strong_tier_is_never_called(self):
        cheap, strong = SpyTier(GOOD), SpyTier(GOOD)
        gate = TieredEscalationGate(
            [Tier("cheap", cheap), Tier("strong", strong)], check=is_grounded
        )

        answer = gate.answer("toy prompt")

        self.assertEqual(answer.answered_by, "cheap")
        self.assertEqual(cheap.calls, 1)
        self.assertEqual(strong.calls, 0)

    def test_a_failing_cheap_tier_escalates_and_the_strong_tier_answers(self):
        cheap, strong = SpyTier(UNGROUNDED), SpyTier(GOOD)
        gate = TieredEscalationGate(
            [Tier("cheap", cheap), Tier("strong", strong)], check=is_grounded
        )

        answer = gate.answer("toy prompt")

        self.assertEqual(answer.answered_by, "strong")
        self.assertEqual(answer.value, GOOD)
        self.assertEqual(cheap.calls, 1)
        self.assertEqual(strong.calls, 1)

    def test_the_ledger_records_which_tier_answered_and_which_were_tried(self):
        cheap, strong = SpyTier(UNGROUNDED), SpyTier(GOOD)
        gate = TieredEscalationGate(
            [Tier("cheap", cheap), Tier("strong", strong)], check=is_grounded
        )

        gate.answer("toy prompt")

        recorded = gate.ledger[-1]
        self.assertEqual(recorded.answered_by, "strong")
        self.assertEqual(
            [(a.tier, a.passed) for a in recorded.attempts],
            [("cheap", False), ("strong", True)],
        )

    def test_failing_output_is_never_returned_even_when_every_tier_fails(self):
        cheap, strong = SpyTier(UNGROUNDED), SpyTier(UNGROUNDED)
        gate = TieredEscalationGate(
            [Tier("cheap", cheap), Tier("strong", strong)], check=is_grounded
        )

        with self.assertRaises(NoTierPassed) as ctx:
            gate.answer("toy prompt")

        self.assertEqual(ctx.exception.reason, "no_tier_passed")
        self.assertEqual([a.tier for a in ctx.exception.attempts], ["cheap", "strong"])
        self.assertEqual(gate.ledger, [])  # nothing was accepted

    def test_a_tier_that_raises_is_escalated_past_not_propagated(self):
        cheap, strong = SpyTier(None, raises=True), SpyTier(GOOD)
        gate = TieredEscalationGate(
            [Tier("cheap", cheap), Tier("strong", strong)], check=is_grounded
        )

        answer = gate.answer("toy prompt")

        self.assertEqual(answer.answered_by, "strong")
        self.assertEqual(
            [(a.tier, a.passed) for a in answer.attempts],
            [("cheap", False), ("strong", True)],
        )

    def test_the_expensive_tier_faces_the_same_check_as_the_cheap_one(self):
        # Cost does not buy trust: a strong tier whose output fails is rejected
        # exactly as a cheap one would be.
        strong = SpyTier(UNGROUNDED)
        gate = TieredEscalationGate([Tier("strong", strong)], check=is_grounded)

        with self.assertRaises(NoTierPassed):
            gate.answer("toy prompt")

        self.assertEqual(strong.calls, 1)

    def test_at_least_one_tier_is_required(self):
        with self.assertRaises(ValueError):
            TieredEscalationGate([], check=is_grounded)


if __name__ == "__main__":
    unittest.main()
