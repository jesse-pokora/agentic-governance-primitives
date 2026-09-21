import inspect
import unittest

from revision_ledger import NoRevisionsRecorded, RevisionLedger


class TrustedRevisionAnchorTests(unittest.TestCase):
    def test_current_returns_the_latest_recorded_commit(self):
        ledger = RevisionLedger()
        ledger.record("commit-a")
        ledger.record("commit-b")
        ledger.record("commit-c")

        self.assertEqual(ledger.current(), "commit-c")

    def test_current_raises_when_nothing_has_been_recorded(self):
        ledger = RevisionLedger()
        with self.assertRaises(NoRevisionsRecorded):
            ledger.current()

    def test_current_accepts_no_caller_supplied_argument_at_all(self):
        # The API structurally cannot be told "trust this commit as
        # current" — current() takes no parameters beyond self.
        params = inspect.signature(RevisionLedger.current).parameters
        self.assertEqual(list(params), ["self"])

    def test_freshness_is_ledger_position_not_recorded_order_of_arrival(self):
        ledger = RevisionLedger()
        ledger.record("commit-a")
        ledger.record("commit-b")

        self.assertFalse(ledger.is_fresh("commit-a"))
        self.assertTrue(ledger.is_fresh("commit-b"))

    def test_an_earlier_commit_never_becomes_fresh_again_by_being_reasserted_as_current(self):
        ledger = RevisionLedger()
        ledger.record("commit-a")
        ledger.record("commit-b")
        ledger.record("commit-c")

        # commit-a is not fresh even though it might be a caller's favorite
        # or "most recently deployed" by some external, out-of-band notion.
        self.assertFalse(ledger.is_fresh("commit-a"))
        self.assertEqual(ledger.current(), "commit-c")

    def test_unknown_commit_is_never_fresh(self):
        ledger = RevisionLedger()
        ledger.record("commit-a")

        self.assertFalse(ledger.is_fresh("commit-never-recorded"))


if __name__ == "__main__":
    unittest.main()
