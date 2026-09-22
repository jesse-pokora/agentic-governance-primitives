import unittest

from rollback import AttestedCheckpointStore, RollbackDenied, digest_of

STATE_V1 = {"config": {"replicas": 1}, "release": "toy-v1"}
STATE_V2 = {"config": {"replicas": 4}, "release": "toy-v2"}
STATE_V3 = {"config": {"replicas": 9}, "release": "toy-v3"}


class AttestedRollbackTests(unittest.TestCase):
    def setUp(self):
        self.store = AttestedCheckpointStore()
        self.v1 = self.store.attest(STATE_V1)
        self.v2 = self.store.attest(STATE_V2)

    def test_rollback_restores_the_attested_state_exactly(self):
        restored = self.store.rollback(self.v1)

        self.assertEqual(restored, STATE_V1)
        self.assertEqual(digest_of(restored), self.v1)
        self.assertEqual(self.store.current_digest, self.v1)

    def test_a_state_that_was_never_attested_cannot_be_rolled_back_to(self):
        # The digest is correct for a real state — it was just never attested
        # in this store.
        never_attested = digest_of(STATE_V3)

        with self.assertRaises(RollbackDenied) as ctx:
            self.store.rollback(never_attested)

        self.assertEqual(ctx.exception.reason, "unattested_target")
        self.assertEqual(self.store.current_digest, self.v2)  # unchanged

    def test_a_corrupted_checkpoint_is_refused_rather_than_restored(self):
        # The bytes filed under v1's digest are substituted; the index still
        # says "this is v1". Trusting the index alone would restore the wrong
        # state under a trusted name.
        self.store._by_digest[self.v1] = '{"release":"toy-substituted"}'

        with self.assertRaises(RollbackDenied) as ctx:
            self.store.rollback(self.v1)

        self.assertEqual(ctx.exception.reason, "restored_digest_mismatch")
        self.assertEqual(self.store.current_digest, self.v2)  # unchanged

    def test_rollback_on_an_empty_store_is_denied(self):
        with self.assertRaises(RollbackDenied) as ctx:
            AttestedCheckpointStore().rollback(digest_of(STATE_V1))

        self.assertEqual(ctx.exception.reason, "no_checkpoints")

    def test_attesting_the_same_state_twice_yields_the_same_digest(self):
        again = self.store.attest(dict(STATE_V1))

        self.assertEqual(again, self.v1)
        self.assertEqual(len(self.store.attested_digests), 2)  # no second copy

    def test_every_attested_state_remains_a_legal_target_after_a_rollback(self):
        self.store.rollback(self.v1)

        self.assertEqual(self.store.rollback(self.v2), STATE_V2)
        self.assertEqual(self.store.current_digest, self.v2)


if __name__ == "__main__":
    unittest.main()
