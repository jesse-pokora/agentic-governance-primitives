import unittest

from lock_manager import ExecutionLockManager, LockHeld, RecoveryDenied


class ExecutionLockAndRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.manager = ExecutionLockManager()

    def test_acquire_returns_a_challenge_and_locks_the_run(self):
        challenge = self.manager.acquire("run-1")
        self.assertTrue(self.manager.is_locked("run-1"))
        self.assertIsInstance(challenge, str)
        self.assertGreater(len(challenge), 0)

    def test_reacquiring_a_held_lock_is_denied_simulating_a_crashed_run(self):
        self.manager.acquire("run-1")
        # run-1's process crashed; nothing tells the manager that, so a
        # second attempt to run it must still be denied.
        with self.assertRaises(LockHeld):
            self.manager.acquire("run-1")

    def test_clearing_with_wrong_challenge_is_denied_and_lock_remains(self):
        self.manager.acquire("run-1")

        with self.assertRaises(RecoveryDenied) as ctx:
            self.manager.clear("run-1", "guessed-challenge")
        self.assertEqual(ctx.exception.reason, "challenge_mismatch")
        self.assertTrue(self.manager.is_locked("run-1"))

    def test_clearing_with_the_correct_challenge_allows_reacquire(self):
        challenge = self.manager.acquire("run-1")
        self.manager.clear("run-1", challenge)

        self.assertFalse(self.manager.is_locked("run-1"))
        self.manager.acquire("run-1")  # succeeds, no exception

    def test_clearing_a_run_with_no_lock_is_denied(self):
        with self.assertRaises(RecoveryDenied) as ctx:
            self.manager.clear("never-locked", "anything")
        self.assertEqual(ctx.exception.reason, "no_lock_held")

    def test_manager_exposes_no_liveness_or_timeout_based_recovery_path(self):
        # The only way to clear a lock is the exact-challenge `clear` method
        # — there is no expiry, ping, or PID-check API at all.
        public_methods = {name for name in dir(ExecutionLockManager) if not name.startswith("_")}
        self.assertEqual(public_methods, {"is_locked", "acquire", "clear"})


if __name__ == "__main__":
    unittest.main()
