import unittest

from mechanism import MECHANISMS, Incomparable, compare, record


class MechanismAttributionTests(unittest.TestCase):
    def test_a_stronger_mechanism_that_rescues_adherence_is_identified(self):
        prose = record("r1", "INS-001", "prose", followed=False)
        gate = record("r2", "INS-001", "gate", followed=True)

        comparison = compare(prose, gate)

        self.assertEqual(comparison.verdict, "stronger_mechanism_helped")
        self.assertEqual((comparison.weaker, comparison.stronger), ("prose", "gate"))

    def test_an_instruction_followed_under_prose_alone_needs_no_gate(self):
        comparison = compare(
            record("r1", "INS-002", "prose", followed=True),
            record("r2", "INS-002", "gate", followed=True),
        )

        self.assertEqual(comparison.verdict, "weaker_sufficed")

    def test_an_instruction_ignored_under_both_is_no_difference(self):
        comparison = compare(
            record("r1", "INS-003", "prose", followed=False),
            record("r2", "INS-003", "hook", followed=False),
        )

        self.assertEqual(comparison.verdict, "no_difference")

    def test_a_result_with_no_recorded_mechanism_cannot_be_compared(self):
        with self.assertRaises(Incomparable) as ctx:
            compare(
                record("r1", "INS-001", None, followed=False),
                record("r2", "INS-001", "gate", followed=True),
            )

        self.assertEqual(ctx.exception.reason, "mechanism_not_recorded")
        self.assertEqual(ctx.exception.detail, "r1")

    def test_an_unrecorded_mechanism_is_allowed_to_be_recorded_as_unknown(self):
        # None is a fact about the observation, not a missing field. It is
        # accepted, and it is what makes the comparison refuse later.
        result = record("r1", "INS-001", None, followed=True)

        self.assertIsNone(result.mechanism)

    def test_two_results_under_the_same_mechanism_are_not_a_mechanism_comparison(self):
        with self.assertRaises(Incomparable) as ctx:
            compare(
                record("r1", "INS-001", "gate", followed=True),
                record("r2", "INS-001", "gate", followed=False),
            )

        self.assertEqual(ctx.exception.reason, "same_mechanism")

    def test_results_about_different_instructions_are_refused(self):
        with self.assertRaises(Incomparable) as ctx:
            compare(
                record("r1", "INS-001", "prose", followed=True),
                record("r2", "INS-002", "gate", followed=True),
            )

        self.assertEqual(ctx.exception.reason, "different_instructions")

    def test_a_mechanism_outside_the_vocabulary_is_refused(self):
        with self.assertRaises(Incomparable) as ctx:
            record("r1", "INS-001", "vibes", followed=True)

        self.assertEqual(ctx.exception.reason, "unknown_mechanism")

    def test_the_comparison_orders_by_mechanism_strength_not_argument_order(self):
        gate = record("r2", "INS-001", "gate", followed=True)
        prose = record("r1", "INS-001", "prose", followed=False)

        self.assertEqual(compare(gate, prose).weaker, "prose")
        self.assertEqual(compare(prose, gate).weaker, "prose")

    def test_the_vocabulary_runs_from_least_to_most_binding(self):
        self.assertEqual(MECHANISMS[0], "prose")
        self.assertEqual(MECHANISMS[-1], "host")
        self.assertLess(MECHANISMS.index("skill"), MECHANISMS.index("gate"))


if __name__ == "__main__":
    unittest.main()
