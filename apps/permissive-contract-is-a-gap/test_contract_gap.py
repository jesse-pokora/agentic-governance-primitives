import unittest

from contract_gap import ContractRejected, Rule, audit, gaps, string_schema

NON_EMPTY = Rule(
    id="RS-109",
    text="A prompt must be a string of at least one character",
    forbidden_examples=("", 123, None),
)
NOT_WHITESPACE = Rule(
    id="RS-111",
    text="A prompt must carry content, not only whitespace",
    forbidden_examples=("   ", "\t", "\n"),
)


class PermissiveContractTests(unittest.TestCase):
    def test_a_contract_that_rejects_every_forbidden_value_is_enforced(self):
        contract = string_schema(min_length=1, pattern=r"\S.*")

        findings = audit(contract, [NON_EMPTY, NOT_WHITESPACE])

        self.assertEqual([f.status for f in findings], ["enforced", "enforced"])
        self.assertEqual(gaps(findings), ())

    def test_a_contract_that_admits_a_forbidden_value_is_a_gap(self):
        # min_length=1 rejects "", so RS-109 holds — but whitespace-only
        # strings sail through, which is exactly RS-111's concern.
        contract = string_schema(min_length=1)

        findings = audit(contract, [NON_EMPTY, NOT_WHITESPACE])

        self.assertEqual([f.status for f in findings], ["enforced", "contract_gap"])
        self.assertEqual(gaps(findings)[0].rule_id, "RS-111")

    def test_the_gap_names_the_values_the_contract_admits(self):
        findings = audit(string_schema(min_length=1), [NOT_WHITESPACE])

        self.assertEqual(len(gaps(findings)[0].admitted), 3)
        self.assertIn("'   '", gaps(findings)[0].admitted)

    def test_no_artifact_is_consulted(self):
        # The audit takes a contract and rules. There is nowhere to pass a
        # sample, because a well-behaved sample is not evidence about what the
        # contract permits.
        import inspect

        signature = inspect.signature(audit)
        self.assertEqual(list(signature.parameters), ["contract", "rules"])

    def test_a_gap_is_reported_even_though_every_real_value_is_fine(self):
        contract = string_schema(min_length=0)
        real_traffic = ["summarize the repo", "list the toy paths", "explain the tests"]

        self.assertTrue(all(contract(value) for value in real_traffic))
        self.assertEqual(len(gaps(audit(contract, [NON_EMPTY]))), 1)

    def test_a_permissive_contract_fails_several_rules_at_once(self):
        findings = audit(string_schema(min_length=0), [NON_EMPTY, NOT_WHITESPACE])

        self.assertEqual(len(gaps(findings)), 2)

    def test_a_rule_that_forbids_nothing_is_refused(self):
        with self.assertRaises(ContractRejected) as ctx:
            Rule(id="RS-000", text="be sensible", forbidden_examples=())

        self.assertEqual(ctx.exception.reason, "rule_forbids_nothing")

    def test_auditing_against_no_rules_is_refused(self):
        with self.assertRaises(ContractRejected) as ctx:
            audit(string_schema(min_length=1), [])

        self.assertEqual(ctx.exception.reason, "no_rules")

    def test_every_rule_produces_exactly_one_finding(self):
        findings = audit(string_schema(min_length=1), [NON_EMPTY, NOT_WHITESPACE])

        self.assertEqual([f.rule_id for f in findings], ["RS-109", "RS-111"])
        self.assertEqual(len(findings), 2)

    def test_a_non_string_is_forbidden_by_the_type_check_itself(self):
        findings = audit(string_schema(min_length=1), [NON_EMPTY])

        self.assertEqual(findings[0].status, "enforced")


if __name__ == "__main__":
    unittest.main()
