import unittest

from ledger import AuthenticatedTransitionLedger


class AuthenticatedTransitionLedgerTests(unittest.TestCase):
    def setUp(self):
        self.ledger = AuthenticatedTransitionLedger(secret_key=b"toy-shared-secret")
        self.ledger.append({"actor": "agent-1", "action": "provision", "target": "svc-fake-a"})
        self.ledger.append({"actor": "agent-2", "action": "deploy", "target": "svc-fake-b"})
        self.ledger.append({"actor": "agent-1", "action": "rollback", "target": "svc-fake-a"})

    def test_untampered_chain_verifies(self):
        result = self.ledger.verify()
        self.assertTrue(result.valid)
        self.assertIsNone(result.first_bad_index)

    def test_editing_one_byte_in_an_early_entry_is_detected_not_just_the_last_row(self):
        # Flip a single character in entry 0's payload, well before the tail,
        # without recomputing its entry_hash or hmac_sig.
        self.ledger.entries[0].payload["target"] = "svc-fake-a-TAMPERED"

        result = self.ledger.verify()
        self.assertFalse(result.valid)
        self.assertEqual(result.first_bad_index, 0)
        self.assertEqual(result.reason, "hash_mismatch")

    def test_forged_entry_hash_without_secret_fails_hmac_check(self):
        # A more careful attacker recomputes entry_hash to match the tampered
        # payload (so the hash check alone would pass) but cannot forge a
        # valid hmac without the secret key.
        entry = self.ledger.entries[1]
        entry.payload["action"] = "delete"
        from ledger import canonical_json
        import hashlib

        entry.entry_hash = hashlib.sha256(
            (entry.prev_hash + canonical_json(entry.payload)).encode("utf-8")
        ).hexdigest()
        # hmac_sig deliberately left stale — attacker doesn't know the secret.

        result = self.ledger.verify()
        self.assertFalse(result.valid)
        self.assertEqual(result.first_bad_index, 1)
        self.assertEqual(result.reason, "hmac_mismatch")

    def test_broken_chain_link_is_detected(self):
        self.ledger.entries[2].prev_hash = "f" * 64

        result = self.ledger.verify()
        self.assertFalse(result.valid)
        self.assertEqual(result.first_bad_index, 2)
        self.assertEqual(result.reason, "chain_broken")


if __name__ == "__main__":
    unittest.main()
