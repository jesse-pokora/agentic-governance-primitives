import unittest

from budget import BoundedExecutionBudget, BudgetDenied, Charge


class SpyAction:
    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return "toy-action-result"


class FakeClock:
    """An injected monotonic clock, so time-bounded behaviour is exact rather
    than dependent on how fast the test machine happens to be."""

    def __init__(self, start=0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, ticks):
        self.now += ticks


class BoundedExecutionBudgetTests(unittest.TestCase):
    def setUp(self):
        self.limits = {"tool_calls": 3, "cost_units": 100}
        self.budget = BoundedExecutionBudget(self.limits)
        self.action = SpyAction()

    def test_actions_inside_the_budget_all_run(self):
        for _ in range(3):
            self.budget.run(Charge("tool_calls", 1), self.action)

        self.assertEqual(self.action.calls, 3)
        self.assertEqual(self.budget.spent("tool_calls"), 3)
        self.assertEqual(self.budget.remaining("tool_calls"), 0)

    def test_the_action_that_would_cross_the_cap_never_runs(self):
        for _ in range(3):
            self.budget.run(Charge("tool_calls", 1), self.action)

        with self.assertRaises(BudgetDenied) as ctx:
            self.budget.run(Charge("tool_calls", 1), self.action)

        self.assertEqual(ctx.exception.reason, "budget_exhausted")
        self.assertIn("tool_calls", ctx.exception.detail)
        self.assertEqual(self.action.calls, 3)

    def test_a_single_oversized_action_is_refused_whole_not_partially_charged(self):
        with self.assertRaises(BudgetDenied):
            self.budget.run(Charge("cost_units", 250), self.action)

        self.assertEqual(self.action.calls, 0)
        self.assertEqual(self.budget.spent("cost_units"), 0)
        self.assertEqual(self.budget.remaining("cost_units"), 100)

    def test_the_run_halts_and_a_later_affordable_action_is_still_denied(self):
        with self.assertRaises(BudgetDenied):
            self.budget.run(Charge("cost_units", 250), self.action)

        self.assertTrue(self.budget.halted)

        # cost_units has 100 left and tool_calls has 3 — both would fit — but
        # the run is over.
        with self.assertRaises(BudgetDenied) as ctx:
            self.budget.run(Charge("tool_calls", 1), self.action)

        self.assertEqual(ctx.exception.reason, "run_halted")
        self.assertEqual(self.action.calls, 0)

    def test_an_undeclared_resource_is_denied_not_treated_as_unlimited(self):
        with self.assertRaises(BudgetDenied) as ctx:
            self.budget.run(Charge("gpu_seconds", 1), self.action)

        self.assertEqual(ctx.exception.reason, "unknown_resource")
        self.assertEqual(self.action.calls, 0)

    def test_a_nonpositive_charge_is_rejected(self):
        with self.assertRaises(BudgetDenied) as ctx:
            self.budget.run(Charge("tool_calls", 0), self.action)

        self.assertEqual(ctx.exception.reason, "invalid_amount")
        self.assertEqual(self.action.calls, 0)

    def test_an_action_past_the_deadline_never_starts(self):
        clock = FakeClock(start=0)
        budget = BoundedExecutionBudget(
            {"tool_calls": 10}, clock=clock, deadline=50
        )

        budget.run(Charge("tool_calls", 1), self.action)
        clock.advance(50)

        with self.assertRaises(BudgetDenied) as ctx:
            budget.run(Charge("tool_calls", 1), self.action)

        self.assertEqual(ctx.exception.reason, "deadline_exceeded")
        self.assertEqual(self.action.calls, 1)

    def test_a_resource_consumed_by_a_failing_action_is_not_refunded(self):
        def explodes():
            raise RuntimeError("toy tool failure")

        with self.assertRaises(RuntimeError):
            self.budget.run(Charge("tool_calls", 1), explodes)

        self.assertEqual(self.budget.spent("tool_calls"), 1)

    def test_mutating_the_source_limits_after_construction_raises_no_cap(self):
        self.limits["tool_calls"] = 9999

        for _ in range(3):
            self.budget.run(Charge("tool_calls", 1), self.action)

        with self.assertRaises(BudgetDenied) as ctx:
            self.budget.run(Charge("tool_calls", 1), self.action)

        self.assertEqual(ctx.exception.reason, "budget_exhausted")


if __name__ == "__main__":
    unittest.main()
