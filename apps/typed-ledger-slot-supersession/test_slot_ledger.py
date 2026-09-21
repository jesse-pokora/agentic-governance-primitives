import unittest

from slot_ledger import SupersessionDenied, TypedLedgerSlots, digest_of


class TypedLedgerSlotSupersessionTests(unittest.TestCase):
    def setUp(self):
        self.ledger = TypedLedgerSlots()

    def test_create_then_supersede_with_the_correct_predecessor_digest_succeeds(self):
        original = self.ledger.create("policy-a", {"version": 1})
        updated = self.ledger.supersede("policy-a", original.digest, {"version": 2})

        self.assertEqual(self.ledger.get("policy-a"), updated)
        self.assertEqual(updated.value, {"version": 2})

    def test_supersede_with_a_forked_wrong_digest_fails_closed(self):
        self.ledger.create("policy-a", {"version": 1})
        wrong_digest = digest_of({"version": 999})  # a value never actually stored

        with self.assertRaises(SupersessionDenied) as ctx:
            self.ledger.supersede("policy-a", wrong_digest, {"version": 2})
        self.assertEqual(ctx.exception.reason, "predecessor_digest_mismatch")

    def test_supersede_of_a_slot_that_was_never_created_fails_closed(self):
        with self.assertRaises(SupersessionDenied) as ctx:
            self.ledger.supersede("never-created", digest_of({"version": 1}), {"version": 2})
        self.assertEqual(ctx.exception.reason, "missing_predecessor")

    def test_create_on_an_existing_slot_key_is_denied(self):
        self.ledger.create("policy-a", {"version": 1})
        with self.assertRaises(SupersessionDenied) as ctx:
            self.ledger.create("policy-a", {"version": 1})
        self.assertEqual(ctx.exception.reason, "slot_already_exists")

    def test_a_stale_predecessor_digest_from_an_earlier_generation_is_rejected(self):
        gen0 = self.ledger.create("policy-a", {"version": 1})
        self.ledger.supersede("policy-a", gen0.digest, {"version": 2})

        # Replaying gen0's digest after the slot has already moved to gen1
        # must fail closed, not silently rewind the slot.
        with self.assertRaises(SupersessionDenied) as ctx:
            self.ledger.supersede("policy-a", gen0.digest, {"version": 3})
        self.assertEqual(ctx.exception.reason, "predecessor_digest_mismatch")
        self.assertEqual(self.ledger.get("policy-a").value, {"version": 2})


if __name__ == "__main__":
    unittest.main()
