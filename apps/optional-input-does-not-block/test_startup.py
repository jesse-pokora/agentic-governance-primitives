import unittest

from startup import InputSpec, StartupRefused, evaluate_startup

SPECS = [
    InputSpec("prompt", required=True),
    InputSpec("run_id", required=False),
    InputSpec("head_commit", required=False),
    InputSpec("evidence_packet", required=False),
    InputSpec("approval_record", required=False),
]


class OptionalInputDoesNotBlockTests(unittest.TestCase):
    def test_a_full_envelope_starts_undegraded(self):
        decision = evaluate_startup(SPECS, {
            "prompt": "summarize the toy repository", "run_id": "r-1",
            "head_commit": "a" * 40, "evidence_packet": {"k": 1},
            "approval_record": {"by": "toy-human"},
        })
        self.assertTrue(decision.started)
        self.assertFalse(decision.degraded)
        self.assertEqual(decision.missing_optional, ())

    def test_a_bare_prompt_is_sufficient_intake(self):
        # Every optional input absent. This is the case the catalog's other
        # apps would be tempted to refuse.
        decision = evaluate_startup(SPECS, {"prompt": "summarize the toy repository"})

        self.assertTrue(decision.started)
        self.assertTrue(decision.degraded)
        self.assertEqual(
            decision.missing_optional,
            ("approval_record", "evidence_packet", "head_commit", "run_id"),
        )

    def test_the_degraded_start_records_what_was_missing(self):
        decision = evaluate_startup(SPECS, {"prompt": "toy", "run_id": "r-1"})

        self.assertTrue(decision.degraded)
        self.assertIn("head_commit", decision.missing_optional)
        self.assertNotIn("run_id", decision.missing_optional)

    def test_a_missing_required_input_refuses(self):
        with self.assertRaises(StartupRefused) as ctx:
            evaluate_startup(SPECS, {"run_id": "r-1"})

        self.assertEqual(ctx.exception.reason, "missing_required_input")
        self.assertEqual(ctx.exception.missing, ("prompt",))

    def test_every_missing_required_input_is_reported_at_once(self):
        specs = SPECS + [InputSpec("target", required=True)]

        with self.assertRaises(StartupRefused) as ctx:
            evaluate_startup(specs, {})

        self.assertEqual(ctx.exception.missing, ("prompt", "target"))

    def test_a_required_input_that_is_present_but_empty_is_missing(self):
        for empty in ("", None, [], {}):
            with self.subTest(empty=empty):
                with self.assertRaises(StartupRefused):
                    evaluate_startup(SPECS, {"prompt": empty})

    def test_a_whitespace_only_required_input_counts_as_present(self):
        # Deliberate: emptiness is length, not meaning. Stripping here would
        # make the gate's answer depend on a judgment about content, which is
        # exactly what a deterministic intake check should not do.
        decision = evaluate_startup(SPECS, {"prompt": "   "})

        self.assertTrue(decision.started)

    def test_an_undeclared_field_is_context_not_a_violation(self):
        decision = evaluate_startup(SPECS, {"prompt": "toy", "workspace_hint": "/toy"})

        self.assertTrue(decision.started)
        self.assertEqual(decision.extra_context, ("workspace_hint",))

    def test_an_empty_optional_is_not_carried_into_the_run(self):
        decision = evaluate_startup(SPECS, {"prompt": "toy", "run_id": ""})

        self.assertNotIn("run_id", decision.supplied)
        self.assertIn("run_id", decision.missing_optional)


if __name__ == "__main__":
    unittest.main()
