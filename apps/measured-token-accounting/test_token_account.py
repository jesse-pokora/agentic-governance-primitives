import unittest

from token_account import (
    AccountingRejected,
    TokenAccount,
    Usage,
    ZERO_USAGE,
)


class MeasuredTokenAccountingTests(unittest.TestCase):
    def setUp(self):
        self.account = TokenAccount()

    def test_measured_calls_sum_to_the_running_total(self):
        self.account.record("call-1", Usage(100, 20))
        self.account.record("call-2", Usage(50, 10))

        total = self.account.total()
        self.assertEqual(total.prompt_tokens, 150)
        self.assertEqual(total.completion_tokens, 30)
        self.assertEqual(total.total_tokens, 180)

    def test_an_unmeasured_call_is_refused_not_counted_as_zero(self):
        self.account.record("call-1", Usage(100, 20))

        with self.assertRaises(AccountingRejected) as ctx:
            self.account.record("call-2", None)

        self.assertEqual(ctx.exception.reason, "unmeasured_call")
        self.assertEqual(self.account.call_count, 1)

    def test_a_genuinely_zero_token_call_is_measured_and_recorded(self):
        # 0 is a measurement; None is the absence of one. The account must
        # tell them apart.
        self.account.record("call-1", ZERO_USAGE)

        self.assertEqual(self.account.call_count, 1)
        self.assertEqual(self.account.total(), ZERO_USAGE)

    def test_recording_the_same_call_twice_is_refused(self):
        self.account.record("call-1", Usage(100, 20))

        with self.assertRaises(AccountingRejected) as ctx:
            self.account.record("call-1", Usage(100, 20))

        self.assertEqual(ctx.exception.reason, "duplicate_call")
        self.assertEqual(self.account.total().total_tokens, 120)

    def test_negative_usage_is_refused(self):
        with self.assertRaises(AccountingRejected) as ctx:
            self.account.record("call-1", Usage(-1, 20))

        self.assertEqual(ctx.exception.reason, "invalid_usage")

    def test_an_empty_call_id_is_refused(self):
        with self.assertRaises(AccountingRejected) as ctx:
            self.account.record("", Usage(1, 1))

        self.assertEqual(ctx.exception.reason, "invalid_call_id")

    def test_matching_parts_reconcile_with_the_provider_total(self):
        self.account.record("call-1", Usage(100, 20))
        self.account.record("call-2", Usage(50, 10))

        self.account.reconcile(Usage(150, 30))  # raises on mismatch

    def test_a_call_the_account_never_saw_shows_up_as_a_mismatch(self):
        self.account.record("call-1", Usage(100, 20))
        # The provider bills for a second call this account was never told about.
        with self.assertRaises(AccountingRejected) as ctx:
            self.account.reconcile(Usage(150, 30))

        self.assertEqual(ctx.exception.reason, "reconciliation_mismatch")
        self.assertIn("measured=120", ctx.exception.detail)
        self.assertIn("reported=180", ctx.exception.detail)

    def test_an_empty_account_reconciles_to_zero(self):
        self.account.reconcile(ZERO_USAGE)


if __name__ == "__main__":
    unittest.main()
