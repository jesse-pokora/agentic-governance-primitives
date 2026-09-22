import unittest

from delegation import DelegationDenied, Grant, effective_authority, may

ROOT = Grant.of("orchestrator", {"repo.read", "repo.write", "deploy.execute"})


class DelegationScopeAttenuationTests(unittest.TestCase):
    def test_an_attenuating_chain_returns_what_survived(self):
        chain = [ROOT,
                 Grant.of("planner-agent", {"repo.read", "repo.write"}),
                 Grant.of("worker-agent", {"repo.read"})]

        self.assertEqual(effective_authority(chain), frozenset({"repo.read"}))

    def test_a_link_claiming_more_than_its_delegator_is_refused(self):
        chain = [ROOT,
                 Grant.of("planner-agent", {"repo.read"}),
                 Grant.of("worker-agent", {"repo.read", "deploy.execute"})]

        with self.assertRaises(DelegationDenied) as ctx:
            effective_authority(chain)

        self.assertEqual(ctx.exception.reason, "amplified_capability")
        self.assertIn("deploy.execute", ctx.exception.detail)
        self.assertIn("depth 2", ctx.exception.detail)

    def test_the_root_may_hold_anything(self):
        self.assertEqual(effective_authority([ROOT]), ROOT.capabilities)

    def test_authority_may_stay_the_same_across_a_link(self):
        chain = [ROOT, Grant.of("planner-agent", ROOT.capabilities)]
        self.assertEqual(effective_authority(chain), ROOT.capabilities)

    def test_amplification_deep_in_a_long_chain_is_still_caught(self):
        chain = [ROOT,
                 Grant.of("a", {"repo.read", "repo.write"}),
                 Grant.of("b", {"repo.read"}),
                 Grant.of("c", {"repo.read"}),
                 Grant.of("d", {"repo.read", "repo.write"})]  # re-acquires write

        with self.assertRaises(DelegationDenied) as ctx:
            effective_authority(chain)

        self.assertIn("repo.write", ctx.exception.detail)
        self.assertIn("depth 4", ctx.exception.detail)

    def test_authority_may_attenuate_to_nothing(self):
        chain = [ROOT, Grant.of("planner-agent", set())]
        self.assertEqual(effective_authority(chain), frozenset())

    def test_a_loop_in_the_chain_is_refused(self):
        chain = [ROOT,
                 Grant.of("planner-agent", {"repo.read"}),
                 Grant.of("orchestrator", {"repo.read"})]

        with self.assertRaises(DelegationDenied) as ctx:
            effective_authority(chain)

        self.assertEqual(ctx.exception.reason, "delegation_loop")

    def test_an_empty_chain_is_refused(self):
        with self.assertRaises(DelegationDenied) as ctx:
            effective_authority([])

        self.assertEqual(ctx.exception.reason, "empty_chain")

    def test_may_answers_only_for_capabilities_that_survived(self):
        chain = [ROOT,
                 Grant.of("planner-agent", {"repo.read", "repo.write"}),
                 Grant.of("worker-agent", {"repo.read"})]

        self.assertTrue(may(chain, "repo.read"))
        self.assertFalse(may(chain, "repo.write"))
        self.assertFalse(may(chain, "deploy.execute"))

    def test_capability_names_are_matched_exactly(self):
        chain = [Grant.of("root", {"repo.read"}), Grant.of("sub", {"repo.read_secrets"})]

        with self.assertRaises(DelegationDenied) as ctx:
            effective_authority(chain)

        self.assertEqual(ctx.exception.reason, "amplified_capability")


if __name__ == "__main__":
    unittest.main()
