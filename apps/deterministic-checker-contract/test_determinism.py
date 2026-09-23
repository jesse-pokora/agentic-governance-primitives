import unittest

from determinism import NondeterministicChecker, certify, evaluate_repeatedly

CLEAN = "result = int(user_input)\n"
DIRTY = "result = eval(user_input)\n"


def pure(source):
    return "passed" if "eval(" not in source else "failed"


class Counting:
    """Returns a different verdict every other call."""

    def __init__(self):
        self.calls = 0

    def __call__(self, source):
        self.calls += 1
        return "passed" if self.calls % 2 else "failed"


class ClockDependent:
    def __init__(self, clock):
        self.clock = clock

    def __call__(self, source):
        self.clock.now += 1
        return "passed" if self.clock.now < 2 else "failed"


class Clock:
    def __init__(self):
        self.now = 0


class DeterministicCheckerTests(unittest.TestCase):
    def test_a_pure_checker_returns_its_verdict(self):
        self.assertEqual(evaluate_repeatedly(pure, CLEAN), "passed")
        self.assertEqual(evaluate_repeatedly(pure, DIRTY), "failed")

    def test_a_checker_that_counts_its_own_calls_is_refused(self):
        with self.assertRaises(NondeterministicChecker) as ctx:
            evaluate_repeatedly(Counting(), CLEAN)

        self.assertEqual(ctx.exception.reason, "verdicts_disagree")

    def test_the_refusal_reports_the_whole_distribution(self):
        with self.assertRaises(NondeterministicChecker) as ctx:
            evaluate_repeatedly(Counting(), CLEAN, runs=5)

        # "Sometimes fails" is not actionable. "3 passed, 2 failed" is.
        self.assertIn("passedx3", ctx.exception.detail)
        self.assertIn("failedx2", ctx.exception.detail)

    def test_a_checker_that_consults_a_clock_is_refused(self):
        with self.assertRaises(NondeterministicChecker) as ctx:
            evaluate_repeatedly(ClockDependent(Clock()), CLEAN)

        self.assertEqual(ctx.exception.reason, "verdicts_disagree")

    def test_one_run_is_refused_because_it_cannot_disagree(self):
        with self.assertRaises(NondeterministicChecker) as ctx:
            evaluate_repeatedly(pure, CLEAN, runs=1)

        self.assertEqual(ctx.exception.reason, "insufficient_runs")

    def test_a_checker_that_raises_names_the_run(self):
        def explodes(source):
            raise RuntimeError("toy checker bug")

        with self.assertRaises(NondeterministicChecker) as ctx:
            evaluate_repeatedly(explodes, CLEAN)

        self.assertEqual(ctx.exception.reason, "checker_errored")
        self.assertIn("run 1", ctx.exception.detail)

    def test_different_verdicts_for_different_artifacts_are_the_point(self):
        self.assertEqual(certify(pure, [CLEAN, DIRTY]), ("passed", "failed"))

    def test_certification_stops_at_the_first_unreproducible_artifact(self):
        flaky = Counting()

        with self.assertRaises(NondeterministicChecker):
            certify(flaky, [CLEAN, DIRTY])

    def test_certifying_nothing_is_refused(self):
        with self.assertRaises(NondeterministicChecker) as ctx:
            certify(pure, [])

        self.assertEqual(ctx.exception.reason, "no_artifacts")

    def test_more_runs_do_not_change_a_stable_verdict(self):
        self.assertEqual(evaluate_repeatedly(pure, DIRTY, runs=25), "failed")


if __name__ == "__main__":
    unittest.main()
