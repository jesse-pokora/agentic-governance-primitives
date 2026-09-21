import unittest

from reconciliation import reconcile


class CanonicalOutcomeReconciliationTests(unittest.TestCase):
    def test_every_key_gets_exactly_one_outcome(self):
        batch = {
            "asset-1": lambda: "ok",
            "asset-2": lambda: (_ for _ in ()).throw(ValueError("bad asset")),
            "asset-3": lambda: "ok",
        }
        outcomes = reconcile(batch)

        self.assertEqual(len(outcomes), len(batch))
        self.assertEqual({o.key for o in outcomes}, set(batch.keys()))

    def test_outcome_order_matches_batch_insertion_order(self):
        batch = {
            "z-asset": lambda: "ok",
            "a-asset": lambda: "ok",
            "m-asset": lambda: "ok",
        }
        outcomes = reconcile(batch)

        self.assertEqual([o.key for o in outcomes], ["z-asset", "a-asset", "m-asset"])

    def test_success_and_failure_are_correctly_attributed(self):
        batch = {
            "good": lambda: "computed-value",
            "bad": lambda: (_ for _ in ()).throw(RuntimeError("exploded")),
        }
        outcomes = {o.key: o for o in reconcile(batch)}

        self.assertEqual(outcomes["good"].status, "success")
        self.assertEqual(outcomes["good"].detail, "computed-value")
        self.assertEqual(outcomes["bad"].status, "failure")
        self.assertIn("exploded", outcomes["bad"].detail)

    def test_empty_batch_yields_empty_outcomes_not_an_error(self):
        self.assertEqual(reconcile({}), [])

    def test_no_key_is_double_counted(self):
        batch = {f"asset-{i}": (lambda: "ok") for i in range(50)}
        outcomes = reconcile(batch)

        keys = [o.key for o in outcomes]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), 50)


if __name__ == "__main__":
    unittest.main()
