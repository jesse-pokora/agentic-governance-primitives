import unittest
from dataclasses import replace

from revert_journal import ForwardOnlyRevertJournal, JournalRejected

V1 = "a" * 64
V2 = "b" * 64
V3 = "c" * 64


class ForwardOnlyRevertJournalTests(unittest.TestCase):
    def setUp(self):
        self.journal = ForwardOnlyRevertJournal()
        self.journal.set_state(V1)
        self.journal.set_state(V2)

    def test_a_revert_appends_a_record_instead_of_erasing_one(self):
        self.journal.revert_to(V1)

        kinds = [record.kind for record in self.journal.records]
        self.assertEqual(kinds, ["set", "set", "revert"])
        self.assertEqual(self.journal.current_digest, V1)

    def test_the_abandoned_state_is_still_readable_afterwards(self):
        self.journal.revert_to(V1)

        # V2 was reverted away from, and is still in the history.
        self.assertIn(V2, self.journal.digests_that_held())
        self.assertEqual(self.journal.records[-1].from_digest, V2)

    def test_reverting_to_a_state_that_never_held_is_refused(self):
        with self.assertRaises(JournalRejected) as ctx:
            self.journal.revert_to(V3)

        self.assertEqual(ctx.exception.reason, "never_held")
        self.assertEqual(self.journal.current_digest, V2)  # unchanged

    def test_reverting_an_empty_journal_is_refused(self):
        with self.assertRaises(JournalRejected) as ctx:
            ForwardOnlyRevertJournal().revert_to(V1)

        self.assertEqual(ctx.exception.reason, "no_history")

    def test_rolling_forward_again_is_just_another_revert_record(self):
        self.journal.revert_to(V1)
        self.journal.revert_to(V2)

        self.assertEqual(self.journal.current_digest, V2)
        self.assertEqual(len(self.journal.records), 4)
        self.assertEqual(self.journal.records[-1].from_digest, V1)
        self.journal.verify()

    def test_a_clean_history_verifies(self):
        self.journal.revert_to(V1)
        self.journal.verify()  # raises on failure

    def test_deleting_a_record_from_the_middle_is_detected(self):
        self.journal.revert_to(V1)
        del self.journal.records[1]

        with self.assertRaises(JournalRejected) as ctx:
            self.journal.verify()

        self.assertEqual(ctx.exception.reason, "index_not_contiguous")

    def test_rewriting_a_record_in_place_is_detected(self):
        self.journal.revert_to(V1)
        # Keep the indices contiguous, change what the middle record says
        # happened — the linkage to the record after it no longer holds.
        self.journal.records[1] = replace(self.journal.records[1], digest=V3)

        with self.assertRaises(JournalRejected) as ctx:
            self.journal.verify()

        self.assertEqual(ctx.exception.reason, "history_rewritten")
        self.assertEqual(ctx.exception.index, 2)

    def test_an_empty_journal_verifies(self):
        ForwardOnlyRevertJournal().verify()


if __name__ == "__main__":
    unittest.main()
