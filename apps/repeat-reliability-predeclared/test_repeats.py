import unittest

from repeats import Plan, Series, SeriesRefused


class RepeatReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.series = Series(plan=Plan(runs=5, configuration="frozen-toy-config"))

    def fill(self, *outcomes):
        for outcome in outcomes:
            self.series.record(outcome)
        return self.series

    def test_a_completed_stable_series_concludes(self):
        conclusion = self.fill(*["passed"] * 5).conclude()

        self.assertTrue(conclusion.stable)
        self.assertEqual(conclusion.outcome, "passed")
        self.assertEqual(conclusion.attempts, 5)

    def test_stopping_early_is_refused(self):
        # Four greens and a temptation to stop.
        self.fill(*["passed"] * 4)

        with self.assertRaises(SeriesRefused) as ctx:
            self.series.conclude()

        self.assertEqual(ctx.exception.reason, "series_incomplete")
        self.assertIn("4 of 5", ctx.exception.detail)

    def test_an_unstable_series_has_no_outcome(self):
        conclusion = self.fill("passed", "passed", "failed", "passed", "passed").conclude()

        self.assertFalse(conclusion.stable)
        self.assertIsNone(conclusion.outcome)

    def test_the_distribution_is_reported_rather_than_a_majority(self):
        # Reporting the majority would turn "fails one time in five" into
        # "passes", which is the entire failure this app exists to prevent.
        conclusion = self.fill("passed", "passed", "failed", "passed", "passed").conclude()

        self.assertEqual(dict(conclusion.distribution), {"passed": 4, "failed": 1})

    def test_every_attempt_is_retained(self):
        self.fill("passed", "failed", "passed", "failed", "passed")

        self.assertEqual(len(self.series.attempts), 5)
        self.assertEqual(self.series.attempts[1], "failed")

    def test_extra_attempts_beyond_the_declaration_are_included(self):
        conclusion = self.fill(*["passed"] * 5, "failed").conclude()

        self.assertEqual(conclusion.attempts, 6)
        self.assertFalse(conclusion.stable)

    def test_the_plan_cannot_be_changed_after_it_is_declared(self):
        with self.assertRaises(Exception):
            self.series.plan.runs = 2

    def test_declaring_a_single_run_is_refused(self):
        with self.assertRaises(SeriesRefused) as ctx:
            Plan(runs=1, configuration="frozen-toy-config")

        self.assertEqual(ctx.exception.reason, "insufficient_declaration")

    def test_an_empty_attempt_is_refused(self):
        with self.assertRaises(SeriesRefused) as ctx:
            self.series.record("")

        self.assertEqual(ctx.exception.reason, "empty_outcome")

    def test_a_series_of_all_failures_is_stable(self):
        # Stable does not mean good. It means the system agrees with itself.
        conclusion = self.fill(*["failed"] * 5).conclude()

        self.assertTrue(conclusion.stable)
        self.assertEqual(conclusion.outcome, "failed")


if __name__ == "__main__":
    unittest.main()
