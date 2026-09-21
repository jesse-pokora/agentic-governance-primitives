import unittest

from approval_gate import ApprovalDenied, approve_and_execute, plan_hash, show_plan


class ExactPlanApprovalGateTests(unittest.TestCase):
    def setUp(self):
        self.plan_text = "DELETE all rows in table `toy_customers` where status='inactive'"
        self.shown = show_plan(self.plan_text)

    def test_exact_hash_approves_and_executes(self):
        result = approve_and_execute(self.plan_text, self.shown.plan_hash)
        self.assertEqual(result, f"executed: {self.plan_text}")

    def test_plain_yes_is_rejected(self):
        with self.assertRaises(ApprovalDenied):
            approve_and_execute(self.plan_text, "yes")

    def test_wrong_hash_is_rejected(self):
        wrong_hash = plan_hash("a completely different plan")
        with self.assertRaises(ApprovalDenied):
            approve_and_execute(self.plan_text, wrong_hash)

    def test_hash_of_stale_plan_is_rejected_after_plan_changes(self):
        stale_hash = self.shown.plan_hash  # hash of the *original* plan
        mutated_plan = self.plan_text + " -- and also drop the audit log"
        with self.assertRaises(ApprovalDenied):
            approve_and_execute(mutated_plan, stale_hash)

    def test_empty_value_is_rejected(self):
        with self.assertRaises(ApprovalDenied):
            approve_and_execute(self.plan_text, "")


if __name__ == "__main__":
    unittest.main()
