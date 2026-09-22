import threading
import unittest

from concurrent_ledger import ConcurrentAppendRejected, ConcurrentLedger

WRITERS = 8


class ConcurrentAppendIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.ledger = ConcurrentLedger()

    def test_uncoordinated_appends_on_a_stale_head_break_the_chain(self):
        # The hazard, staged as an explicit interleaving rather than a race, so
        # the demonstration is deterministic: both writers read the same head
        # before either of them writes.
        head_both_writers_saw = self.ledger.head_hash()
        self.ledger.append_unsafe({"actor": "agent-a"}, head_both_writers_saw)
        self.ledger.append_unsafe({"actor": "agent-b"}, head_both_writers_saw)

        result = self.ledger.verify()

        self.assertFalse(result.valid)
        self.assertEqual(result.reason, "chain_broken")
        self.assertEqual(result.first_bad_index, 1)

    def test_compare_and_swap_rejects_the_writer_whose_head_moved(self):
        head_both_writers_saw = self.ledger.head_hash()
        self.ledger.append_cas({"actor": "agent-a"}, head_both_writers_saw)

        with self.assertRaises(ConcurrentAppendRejected) as ctx:
            self.ledger.append_cas({"actor": "agent-b"}, head_both_writers_saw)

        self.assertEqual(ctx.exception.reason, "head_moved")
        self.assertEqual(len(self.ledger.entries), 1)
        self.assertTrue(self.ledger.verify().valid)

    def test_under_a_real_race_exactly_one_compare_and_swap_writer_wins(self):
        # Every thread reads the head *before* the barrier, so all eight are
        # genuinely building on the same predecessor when they are released.
        barrier = threading.Barrier(WRITERS)
        accepted: list[int] = []
        rejected: list[str] = []
        guard = threading.Lock()

        def writer(n: int):
            expected_head = self.ledger.head_hash()
            barrier.wait()
            try:
                index = self.ledger.append_cas({"actor": f"agent-{n}"}, expected_head)
            except ConcurrentAppendRejected as rejection:
                with guard:
                    rejected.append(rejection.reason)
            else:
                with guard:
                    accepted.append(index)

        threads = [threading.Thread(target=writer, args=(n,)) for n in range(WRITERS)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(accepted), 1)
        self.assertEqual(len(rejected), WRITERS - 1)
        self.assertEqual(set(rejected), {"head_moved"})
        self.assertEqual(len(self.ledger.entries), 1)
        self.assertTrue(self.ledger.verify().valid)

    def test_serialized_appends_all_succeed_with_contiguous_indices(self):
        barrier = threading.Barrier(WRITERS)

        def writer(n: int):
            barrier.wait()
            self.ledger.append_locked({"actor": f"agent-{n}"})

        threads = [threading.Thread(target=writer, args=(n,)) for n in range(WRITERS)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        indices = [entry.index for entry in self.ledger.entries]
        actors = {entry.payload["actor"] for entry in self.ledger.entries}

        self.assertEqual(indices, list(range(WRITERS)))  # no gaps, no duplicates
        self.assertEqual(len(actors), WRITERS)  # nothing lost, nothing doubled
        self.assertTrue(self.ledger.verify().valid)

    def test_a_rejected_append_leaves_no_trace(self):
        self.ledger.append_locked({"actor": "agent-a"})
        before = list(self.ledger.entries)

        with self.assertRaises(ConcurrentAppendRejected):
            self.ledger.append_cas({"actor": "agent-b"}, "f" * 64)

        self.assertEqual(self.ledger.entries, before)

    def test_verification_catches_a_non_contiguous_index(self):
        from dataclasses import replace

        self.ledger.append_locked({"actor": "agent-a"})
        self.ledger.append_locked({"actor": "agent-b"})
        self.ledger.entries[1] = replace(self.ledger.entries[1], index=7)

        result = self.ledger.verify()

        self.assertFalse(result.valid)
        self.assertEqual(result.reason, "index_not_contiguous")
        self.assertEqual(result.first_bad_index, 1)


if __name__ == "__main__":
    unittest.main()
