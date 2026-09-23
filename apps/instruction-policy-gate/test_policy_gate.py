import unittest

from policy_gate import (
    CHECKER_VERDICTS,
    Instruction,
    PolicyRejected,
    evaluate,
)

ARTIFACT = "class Service:\n    def __init__(self, repo):\n        self.repo = repo\n"


def always(verdict, detail=""):
    return lambda artifact: (verdict, detail)


POLICY = [
    Instruction("INS-001", "Constructors receive collaborators", "AGENTS.md:12-14",
                always("passed")),
    Instruction("INS-002", "No module-level singletons", "AGENTS.md:16",
                always("not_applicable", "no module-level assignments in this artifact")),
    Instruction("INS-003", "Write clearly and for the reader", "AGENTS.md:20"),
]


class InstructionPolicyGateTests(unittest.TestCase):
    def test_every_declared_instruction_appears_exactly_once(self):
        report = evaluate(POLICY, ARTIFACT)

        self.assertEqual([v.instruction_id for v in report.verdicts],
                         ["INS-001", "INS-002", "INS-003"])

    def test_an_instruction_with_no_checker_is_unenforceable_not_passed(self):
        report = evaluate(POLICY, ARTIFACT)

        unenforceable = report.of("unenforceable")
        self.assertEqual([v.instruction_id for v in unenforceable], ["INS-003"])
        self.assertNotIn("INS-003", [v.instruction_id for v in report.of("passed")])

    def test_unenforceable_is_never_a_verdict_a_checker_can_return(self):
        # Otherwise an instruction could mark itself unverifiable and vanish
        # from the part of the report anyone reads.
        self.assertNotIn("unenforceable", CHECKER_VERDICTS)

        policy = [Instruction("INS-009", "t", "s", always("unenforceable"))]
        with self.assertRaises(PolicyRejected) as ctx:
            evaluate(policy, ARTIFACT)

        self.assertEqual(ctx.exception.reason, "invalid_verdict")

    def test_coverage_separates_nothing_failed_from_everything_checked(self):
        report = evaluate(POLICY, ARTIFACT)

        self.assertTrue(report.admitted)
        self.assertEqual(report.coverage(), (2, 3))

    def test_not_applicable_is_distinct_from_passed(self):
        report = evaluate(POLICY, ARTIFACT)

        self.assertEqual([v.instruction_id for v in report.of("passed")], ["INS-001"])
        self.assertEqual([v.instruction_id for v in report.of("not_applicable")],
                         ["INS-002"])

    def test_a_failure_blocks_admission_and_is_named(self):
        policy = list(POLICY) + [
            Instruction("INS-004", "No direct construction", "AGENTS.md:22",
                        always("failed", "Service() built at line 7"))
        ]

        report = evaluate(policy, ARTIFACT)

        self.assertFalse(report.admitted)
        self.assertEqual([v.instruction_id for v in report.failures], ["INS-004"])
        self.assertIn("line 7", report.failures[0].detail)

    def test_an_unenforceable_instruction_does_not_block_admission(self):
        # It is not evidence of a violation. It is also not evidence of
        # compliance, which is what coverage reports.
        report = evaluate([POLICY[2]], ARTIFACT)

        self.assertTrue(report.admitted)
        self.assertEqual(report.coverage(), (0, 1))

    def test_a_checker_that_invents_a_verdict_is_refused(self):
        policy = [Instruction("INS-005", "t", "s", always("probably fine"))]

        with self.assertRaises(PolicyRejected) as ctx:
            evaluate(policy, ARTIFACT)

        self.assertEqual(ctx.exception.reason, "invalid_verdict")

    def test_a_checker_that_raises_invalidates_the_report(self):
        def explodes(artifact):
            raise RuntimeError("toy checker bug")

        policy = [Instruction("INS-006", "t", "s", explodes)]

        with self.assertRaises(PolicyRejected) as ctx:
            evaluate(policy, ARTIFACT)

        self.assertEqual(ctx.exception.reason, "checker_errored")

    def test_duplicate_instruction_ids_are_refused(self):
        policy = [POLICY[0], Instruction("INS-001", "other", "s", always("passed"))]

        with self.assertRaises(PolicyRejected) as ctx:
            evaluate(policy, ARTIFACT)

        self.assertEqual(ctx.exception.reason, "duplicate_instruction_id")

    def test_an_empty_policy_is_refused(self):
        with self.assertRaises(PolicyRejected) as ctx:
            evaluate([], ARTIFACT)

        self.assertEqual(ctx.exception.reason, "empty_policy")

    def test_an_instruction_without_an_id_is_refused(self):
        with self.assertRaises(PolicyRejected) as ctx:
            evaluate([Instruction("", "t", "s", always("passed"))], ARTIFACT)

        self.assertEqual(ctx.exception.reason, "unidentified_instruction")


if __name__ == "__main__":
    unittest.main()
