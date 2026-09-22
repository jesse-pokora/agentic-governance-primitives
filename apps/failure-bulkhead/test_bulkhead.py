import unittest

from bulkhead import BreakerOpen, FailureBulkhead


class FakeClock:
    def __init__(self, now=0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, ticks):
        self.now += ticks


class Dependency:
    """Counts every invocation, so 'failed fast' is observable."""

    def __init__(self, healthy=False):
        self.calls = 0
        self.healthy = healthy

    def __call__(self):
        self.calls += 1
        if not self.healthy:
            raise RuntimeError("toy dependency is down")
        return "toy result"


class FailureBulkheadTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.breaker = FailureBulkhead(threshold=3, cooldown=60, clock=self.clock)
        self.dependency = Dependency()

    def fail_times(self, n):
        for _ in range(n):
            with self.assertRaises(RuntimeError):
                self.breaker.call(self.dependency)

    def test_failures_below_the_threshold_still_reach_the_dependency(self):
        self.fail_times(2)

        self.assertEqual(self.dependency.calls, 2)
        self.assertEqual(self.breaker.state, "closed")

    def test_the_threshold_failure_opens_the_breaker(self):
        self.fail_times(3)

        self.assertEqual(self.breaker.state, "open")
        self.assertEqual(self.breaker.history[-1].reason, "threshold_reached")

    def test_an_open_breaker_never_invokes_the_dependency(self):
        self.fail_times(3)
        before = self.dependency.calls

        for _ in range(50):
            with self.assertRaises(BreakerOpen) as ctx:
                self.breaker.call(self.dependency)

        self.assertEqual(ctx.exception.reason, "circuit_open")
        self.assertEqual(self.dependency.calls, before)

    def test_a_success_clears_the_consecutive_count(self):
        self.fail_times(2)
        self.dependency.healthy = True
        self.breaker.call(self.dependency)
        self.dependency.healthy = False
        self.fail_times(2)

        self.assertEqual(self.breaker.state, "closed")

    def test_a_probe_before_the_cooldown_is_refused(self):
        self.fail_times(3)
        self.clock.advance(59)

        with self.assertRaises(BreakerOpen) as ctx:
            self.breaker.probe(self.dependency)

        self.assertEqual(ctx.exception.reason, "cooldown_not_elapsed")

    def test_a_failing_probe_reopens_and_restarts_the_cooldown(self):
        self.fail_times(3)
        self.clock.advance(60)

        with self.assertRaises(RuntimeError):
            self.breaker.probe(self.dependency)

        self.assertEqual(self.breaker.state, "open")
        self.assertEqual(self.breaker.opened_at, 60)
        with self.assertRaises(BreakerOpen) as ctx:
            self.breaker.probe(self.dependency)
        self.assertEqual(ctx.exception.reason, "cooldown_not_elapsed")

    def test_only_a_succeeding_probe_closes_the_breaker(self):
        self.fail_times(3)
        self.clock.advance(60)
        self.dependency.healthy = True

        self.assertEqual(self.breaker.probe(self.dependency), "toy result")
        self.assertEqual(self.breaker.state, "closed")
        self.assertEqual(self.breaker.call(self.dependency), "toy result")

    def test_the_cooldown_elapsing_does_not_by_itself_close_the_breaker(self):
        # A breaker that closed on a timer would decide a service recovered
        # without ever asking it.
        self.fail_times(3)
        self.clock.advance(10_000)

        with self.assertRaises(BreakerOpen) as ctx:
            self.breaker.call(self.dependency)

        self.assertEqual(ctx.exception.reason, "circuit_open")
        self.assertEqual(self.breaker.state, "open")

    def test_probing_a_closed_breaker_is_refused(self):
        with self.assertRaises(BreakerOpen) as ctx:
            self.breaker.probe(self.dependency)

        self.assertEqual(ctx.exception.reason, "not_open")

    def test_every_transition_is_recorded_with_a_reason(self):
        self.fail_times(3)
        self.clock.advance(60)
        self.dependency.healthy = True
        self.breaker.probe(self.dependency)

        self.assertEqual(
            [(t.to, t.reason) for t in self.breaker.history],
            [("open", "threshold_reached"), ("closed", "probe_succeeded")],
        )


if __name__ == "__main__":
    unittest.main()
