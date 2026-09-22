import os
import tempfile
import unittest

# Imported through `pipeline`, which is what puts the sibling apps on the path.
# Importing them directly here would depend on import order to work at all.
from pipeline import (
    GATES,
    Action,
    GovernedCallPath,
    InstructionManifest,
    PinnedInstructionSet,
    RequestRefused,
)

AGENTS_MD = b"# toy agent instructions\nalways state the atomic claim\n"
INSTRUCTIONS = {"AGENTS.md": AGENTS_MD}

GOOD_INTAKE = {"prompt": "summarize svc-fake-a"}
GOOD_ACTION = Action("write_guide", ("summarize-repository",))
GOOD_URL = "https://api.example.test/v1/toy"
CONTENT = "generated guide"


class GovernedCallPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.scope = os.path.join(self.tmp.name, "work")
        os.makedirs(self.scope)
        self.outside = os.path.join(self.tmp.name, "outside")
        os.makedirs(self.outside)

        self.path = GovernedCallPath(
            pinned_instructions=PinnedInstructionSet.pin(
                InstructionManifest.from_files(INSTRUCTIONS)
            ),
            objectives={"summarize-repository"},
            personas={"writer-agent": {"repo.write"}},
            egress_allowlist=["https://api.example.test"],
            scope_root=self.scope,
            limits={"tool_calls": 1},
        )

    def tearDown(self):
        self.tmp.cleanup()

    def handle(self, **overrides):
        request = dict(
            intake=GOOD_INTAKE, instructions=dict(INSTRUCTIONS), action=GOOD_ACTION,
            fetch_url=GOOD_URL, write_path="AGENTS.md", content=CONTENT,
        )
        request.update(overrides)
        return self.path.handle(**request)

    def assert_stopped_at(self, gate, refusal):
        """The named gate refused, and nothing after it in the declared order ran."""
        self.assertEqual(refusal.gate, gate)
        later = GATES[GATES.index(gate) + 1:]
        self.assertFalse(set(self.path.gates_run()) & set(later))

    # --- the request that satisfies everything ---------------------------

    def test_a_compliant_request_passes_every_gate_and_performs_the_effect(self):
        outcome = self.handle()

        self.assertTrue(outcome.performed)
        self.assertEqual([r.gate for r in outcome.gates], list(GATES))
        self.assertTrue(all(r.passed for r in outcome.gates))
        self.assertTrue(os.path.isfile(os.path.join(self.scope, "AGENTS.md")))
        self.assertIn(CONTENT, outcome.document)

    def test_the_gates_run_in_the_declared_order(self):
        self.handle()
        self.assertEqual(self.path.gates_run(), GATES)

    # --- one gate refuses, at each position ------------------------------

    def test_drifted_instructions_stop_the_request_at_the_first_gate(self):
        drifted = {"AGENTS.md": AGENTS_MD.replace(b"always", b"rarely")}

        with self.assertRaises(RequestRefused) as ctx:
            self.handle(instructions=drifted)

        self.assert_stopped_at("instruction-set", ctx.exception)
        self.assertEqual(ctx.exception.reason, "content_drift")
        self.assertEqual(self.path.gates_run(), ("instruction-set",))

    def test_missing_required_intake_stops_at_the_second_gate(self):
        with self.assertRaises(RequestRefused) as ctx:
            self.handle(intake={"run_id": "r-1"})

        self.assert_stopped_at("intake", ctx.exception)
        self.assertEqual(ctx.exception.reason, "missing_required_input")

    def test_an_undeclared_objective_stops_at_the_objective_gate(self):
        with self.assertRaises(RequestRefused) as ctx:
            self.handle(action=Action("write_guide", ("ship-it",)))

        self.assert_stopped_at("objective", ctx.exception)
        self.assertEqual(ctx.exception.reason, "undeclared_objective")

    def test_exhausting_the_budget_stops_at_the_budget_gate(self):
        self.handle()  # spends the single tool call

        with self.assertRaises(RequestRefused) as ctx:
            self.handle()

        self.assertEqual(ctx.exception.gate, "budget")
        self.assertEqual(ctx.exception.reason, "budget_exhausted")

    def test_a_missing_capability_stops_at_the_capability_gate(self):
        self.path.personas = {"writer-agent": {"repo.read"}}

        with self.assertRaises(RequestRefused) as ctx:
            self.handle()

        self.assert_stopped_at("capability", ctx.exception)
        self.assertEqual(ctx.exception.reason, "capability_not_granted")

    def test_an_unlisted_egress_host_stops_at_the_egress_gate(self):
        with self.assertRaises(RequestRefused) as ctx:
            self.handle(fetch_url="https://exfil.evil.test/collect")

        self.assert_stopped_at("egress", ctx.exception)
        self.assertEqual(ctx.exception.reason, "host_not_allowed")

    def test_a_write_outside_the_scope_stops_at_the_write_scope_gate(self):
        escaped = os.path.join(self.outside, "stolen.md")

        with self.assertRaises(RequestRefused) as ctx:
            self.handle(write_path=escaped)

        self.assertEqual(ctx.exception.gate, "write-scope")
        self.assertEqual(ctx.exception.reason, "outside_scope")
        self.assertFalse(os.path.exists(escaped))

    # --- properties of the path as a whole -------------------------------

    def test_a_refused_request_performs_no_effect(self):
        for overrides in (
            {"instructions": {"AGENTS.md": b"drifted\n"}},
            {"intake": {}},
            {"action": Action("write_guide", ("ship-it",))},
            {"fetch_url": "https://exfil.evil.test/collect"},
        ):
            with self.subTest(refusal=sorted(overrides)[0]):
                fresh = GovernedCallPath(
                    pinned_instructions=self.path.pinned_instructions,
                    objectives=set(self.path.objectives),
                    personas=dict(self.path.personas),
                    egress_allowlist=list(self.path.egress_allowlist),
                    scope_root=self.scope,
                    limits={"tool_calls": 1},
                )
                with self.assertRaises(RequestRefused):
                    fresh.handle(
                        intake=overrides.get("intake", GOOD_INTAKE),
                        instructions=overrides.get("instructions", dict(INSTRUCTIONS)),
                        action=overrides.get("action", GOOD_ACTION),
                        fetch_url=overrides.get("fetch_url", GOOD_URL),
                        write_path="AGENTS.md",
                        content=CONTENT,
                    )
                self.assertFalse(os.path.exists(os.path.join(self.scope, "AGENTS.md")))

    def test_the_ledger_records_every_gate_and_verifies(self):
        self.handle()

        self.assertEqual(len(self.path.ledger.entries), len(GATES))
        self.assertTrue(self.path.ledger.verify().valid)

    def test_a_refusal_is_recorded_in_the_ledger_not_only_a_success(self):
        with self.assertRaises(RequestRefused):
            self.handle(fetch_url="https://exfil.evil.test/collect")

        payloads = [e.payload for e in self.path.ledger.entries]
        self.assertEqual(payloads[-1]["verdict"], "refused")
        self.assertEqual(payloads[-1]["gate"], "egress")
        self.assertTrue(self.path.ledger.verify().valid)

    def test_the_evidence_of_a_refused_run_is_tamper_evident_too(self):
        with self.assertRaises(RequestRefused):
            self.handle(action=Action("write_guide", ("ship-it",)))

        self.path.ledger.entries[0].payload["verdict"] = "refused"

        self.assertFalse(self.path.ledger.verify().valid)


if __name__ == "__main__":
    unittest.main()
