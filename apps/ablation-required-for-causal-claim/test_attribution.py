import unittest

from attribution import AttributionRefused, Run, attribute

FACTORS = {"task": "summarize-toy-repo", "model": "toy-model-v2", "corpus": "toy-corpus"}
BOTH = {"INS-001", "INS-002"}


def run(id, instructions, outcome, **factor_overrides):
    return Run.of(id, instructions, dict(FACTORS, **factor_overrides), outcome)


class AblationTests(unittest.TestCase):
    def test_without_a_control_the_finding_is_a_correlation(self):
        finding = attribute("INS-001", run("r1", BOTH, "poor"))

        self.assertEqual(finding.relation, "correlated")
        self.assertIn("not shown to follow from it", finding.detail)

    def test_a_correlation_is_recorded_rather_than_discarded(self):
        finding = attribute("INS-001", run("r1", BOTH, "poor"))

        self.assertEqual(finding.instruction_id, "INS-001")
        self.assertEqual(finding.compared, ("r1",))

    def test_a_clean_leave_one_out_supports_a_causal_claim(self):
        finding = attribute(
            "INS-001",
            run("r1", BOTH, "good"),
            run("r2", {"INS-002"}, "poor"),
        )

        self.assertEqual(finding.relation, "caused")
        self.assertEqual(finding.compared, ("r1", "r2"))

    def test_the_same_outcome_either_way_is_no_effect_not_causation(self):
        finding = attribute(
            "INS-001",
            run("r1", BOTH, "good"),
            run("r2", {"INS-002"}, "good"),
        )

        self.assertEqual(finding.relation, "no_effect")

    def test_a_comparison_that_also_changed_the_model_is_confounded(self):
        with self.assertRaises(AttributionRefused) as ctx:
            attribute(
                "INS-001",
                run("r1", BOTH, "good"),
                run("r2", {"INS-002"}, "poor", model="toy-model-v3"),
            )

        self.assertEqual(ctx.exception.reason, "confounded_comparison")
        self.assertIn("model", ctx.exception.detail)

    def test_the_confound_is_named(self):
        with self.assertRaises(AttributionRefused) as ctx:
            attribute(
                "INS-001",
                run("r1", BOTH, "good"),
                run("r2", {"INS-002"}, "poor", corpus="other", task="other"),
            )

        self.assertIn("corpus", ctx.exception.detail)
        self.assertIn("task", ctx.exception.detail)

    def test_removing_two_instructions_at_once_cannot_attribute_to_one(self):
        with self.assertRaises(AttributionRefused) as ctx:
            attribute("INS-001", run("r1", BOTH, "good"), run("r2", set(), "poor"))

        self.assertEqual(ctx.exception.reason, "multiple_instructions_removed")

    def test_a_control_that_still_has_the_instruction_is_refused(self):
        with self.assertRaises(AttributionRefused) as ctx:
            attribute("INS-001", run("r1", BOTH, "good"), run("r2", BOTH, "poor"))

        self.assertEqual(ctx.exception.reason, "control_retains_instruction")

    def test_attributing_an_instruction_that_was_not_in_effect_is_refused(self):
        with self.assertRaises(AttributionRefused) as ctx:
            attribute("INS-009", run("r1", BOTH, "poor"))

        self.assertEqual(ctx.exception.reason, "instruction_absent_from_treatment")

    def test_a_violation_alongside_a_bad_outcome_is_still_only_correlation(self):
        # The default diagnosis this app exists to refuse: the instruction was
        # violated, the outcome was poor, therefore the violation caused it.
        finding = attribute("INS-001", run("r1", BOTH, "poor"))

        self.assertNotEqual(finding.relation, "caused")


if __name__ == "__main__":
    unittest.main()
