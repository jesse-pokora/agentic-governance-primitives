import unittest

from memory_store import MemoryRecord, MemoryRejected, QuarantiningMemoryStore

ALPHA = MemoryRecord(key="svc-fake-a.owner", value="toy-team-alpha", source="run-1")
ALPHA_AGAIN = MemoryRecord(key="svc-fake-a.owner", value="toy-team-alpha", source="run-2")
BETA = MemoryRecord(key="svc-fake-a.owner", value="toy-team-beta", source="run-3")


class MemoryConflictQuarantineTests(unittest.TestCase):
    def setUp(self):
        self.store = QuarantiningMemoryStore()

    def test_a_first_write_settles(self):
        self.assertTrue(self.store.write(ALPHA))
        self.assertEqual(self.store.read("svc-fake-a.owner"), ALPHA)

    def test_a_contradicting_write_does_not_overwrite_the_held_value(self):
        self.store.write(ALPHA)
        settled = self.store.write(BETA)

        self.assertFalse(settled)
        self.assertEqual(len(self.store.quarantine), 1)
        self.assertEqual(self.store.quarantine[0].held, ALPHA)
        self.assertEqual(self.store.quarantine[0].incoming, BETA)

    def test_a_conflicted_key_has_no_answer_until_it_is_resolved(self):
        self.store.write(ALPHA)
        self.store.write(BETA)

        with self.assertRaises(MemoryRejected) as ctx:
            self.store.read("svc-fake-a.owner")

        self.assertEqual(ctx.exception.reason, "key_in_conflict")

    def test_both_sides_of_the_conflict_stay_attributable(self):
        self.store.write(ALPHA)
        self.store.write(BETA)

        conflict = self.store.quarantine[0]
        self.assertEqual(conflict.held.source, "run-1")
        self.assertEqual(conflict.incoming.source, "run-3")

    def test_an_identical_re_assertion_is_corroboration_not_conflict(self):
        self.store.write(ALPHA)

        self.assertTrue(self.store.write(ALPHA_AGAIN))
        self.assertEqual(self.store.quarantine, [])
        self.assertEqual(self.store.read("svc-fake-a.owner"), ALPHA)

    def test_resolution_settles_the_key(self):
        self.store.write(ALPHA)
        self.store.write(BETA)

        self.store.resolve("svc-fake-a.owner", BETA)

        self.assertEqual(self.store.read("svc-fake-a.owner"), BETA)
        self.assertEqual(self.store.quarantine, [])

    def test_resolution_cannot_introduce_a_value_nobody_asserted(self):
        self.store.write(ALPHA)
        self.store.write(BETA)

        third = MemoryRecord(key="svc-fake-a.owner", value="toy-team-gamma", source="human")
        with self.assertRaises(MemoryRejected) as ctx:
            self.store.resolve("svc-fake-a.owner", third)

        self.assertEqual(ctx.exception.reason, "value_never_asserted")
        self.assertEqual(len(self.store.quarantine), 1)

    def test_resolving_a_key_that_is_not_in_conflict_is_refused(self):
        self.store.write(ALPHA)

        with self.assertRaises(MemoryRejected) as ctx:
            self.store.resolve("svc-fake-a.owner", ALPHA)

        self.assertEqual(ctx.exception.reason, "not_in_conflict")

    def test_reading_an_unknown_key_is_refused(self):
        with self.assertRaises(MemoryRejected) as ctx:
            self.store.read("never-written")

        self.assertEqual(ctx.exception.reason, "unknown_key")

    def test_an_unrelated_key_is_unaffected_by_a_conflict_elsewhere(self):
        other = MemoryRecord(key="svc-fake-b.owner", value="toy-team-beta", source="run-1")
        self.store.write(ALPHA)
        self.store.write(BETA)
        self.store.write(other)

        self.assertEqual(self.store.read("svc-fake-b.owner"), other)


if __name__ == "__main__":
    unittest.main()
