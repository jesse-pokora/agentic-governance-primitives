"""A governed call path.

One request, through every declared gate, in a fixed order. The first gate that
refuses stops it: no later gate runs, no effect occurs, and the ledger records
which gate refused and why.

This is not an app. Every app in `apps/` is one atomic claim and imports
nothing from its siblings. This directory is the exception, and it exists
because a control plane that nothing routes through is documentation: the
primitives have to be shown composing, or the claim that they compose is
untested.

It is also not an orchestrator. There is no router — the order is a constant.
No scheduler, no queue, no second agent, no loop. It is one request passing
through seven gates and then doing one thing, which is the smallest artifact
that can demonstrate composition at all.

Every gate below is the real module from `apps/`, imported unchanged.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

APPS = Path(__file__).resolve().parents[2] / "apps"
for _app in (
    "hash-pinned-instruction-set",
    "optional-input-does-not-block",
    "declared-objective-conformance",
    "bounded-execution-budget",
    "capability-gated-tool-invocation",
    "pinned-egress-allowlist",
    "write-scope-confinement",
    "managed-block-confinement",
    "authenticated-transition-ledger",
):
    sys.path.insert(0, str(APPS / _app))

from budget import BoundedExecutionBudget, Charge  # noqa: E402
from capability_gate import CapabilityGate, ToolSpec  # noqa: E402
from confined_writer import ConfinedWriter  # noqa: E402
from egress import PinnedEgressAllowlist  # noqa: E402
from instruction_set import InstructionManifest, PinnedInstructionSet, verify  # noqa: E402
from ledger import AuthenticatedTransitionLedger  # noqa: E402
from managed_block import write_managed_block  # noqa: E402
from objectives import Action, Run  # noqa: E402
from startup import InputSpec, evaluate_startup  # noqa: E402

GATES = (
    "instruction-set",
    "intake",
    "objective",
    "budget",
    "capability",
    "egress",
    "write-scope",
)


class RequestRefused(Exception):
    def __init__(self, gate: str, reason: str, detail: str = ""):
        super().__init__(f"{gate}: {reason}")
        self.gate = gate
        self.reason = reason
        self.detail = detail


@dataclass
class GateRecord:
    gate: str
    passed: bool
    reason: str = ""


@dataclass
class Outcome:
    performed: bool
    gates: tuple[GateRecord, ...]
    document: str = ""


@dataclass
class GovernedCallPath:
    """Everything the run is allowed to be, declared up front."""

    pinned_instructions: PinnedInstructionSet
    objectives: set[str]
    personas: dict[str, set[str]]
    egress_allowlist: list[str]
    scope_root: str
    limits: dict[str, int]
    ledger_key: bytes = b"toy-shared-secret"

    trace: list[GateRecord] = field(default_factory=list)
    ledger: AuthenticatedTransitionLedger = field(init=False)
    budget: BoundedExecutionBudget = field(init=False)
    run: Run = field(init=False)

    def __post_init__(self) -> None:
        self.ledger = AuthenticatedTransitionLedger(secret_key=self.ledger_key)
        # The budget and the objectives belong to the run, not to one request:
        # a budget rebuilt per request bounds nothing, because every request
        # starts full.
        self.budget = BoundedExecutionBudget(dict(self.limits))
        self.run = Run.declaring(set(self.objectives))

    def _gate(self, name: str, check: Callable[[], Any]) -> Any:
        """Enter one gate, record the verdict either way, and stop on refusal.

        The trace is in the order gates were *entered*, not the order their
        verdicts completed. Three of these gates wrap the rest of the path, so
        their verdicts land innermost-first the way a call stack unwinds —
        entry order is the one a reader means by "the order of the gates".

        Recording happens before the exception escapes, so a refused request
        leaves the same kind of evidence a successful one does. A gate that
        logged only its successes would be useless exactly when it mattered.
        """
        record = GateRecord(gate=name, passed=False)
        self.trace.append(record)

        try:
            result = check()
        except RequestRefused:
            # An inner gate already refused and recorded itself. Attributing
            # its refusal to this gate as well would name the wrong gate in
            # every nested case, which is the whole question a reader has.
            raise
        except Exception as denial:
            reason = str(getattr(denial, "reason", type(denial).__name__))
            record.reason = reason
            self.ledger.append({"gate": name, "verdict": "refused", "reason": reason})
            raise RequestRefused(name, reason, str(getattr(denial, "detail", ""))) from None

        record.passed = True
        self.ledger.append({"gate": name, "verdict": "passed"})
        return result

    def handle(
        self,
        intake: dict,
        instructions: dict[str, bytes],
        action: Action,
        fetch_url: str,
        write_path: str,
        content: str,
    ) -> Outcome:
        """Take one request all the way through, or refuse at the first gate."""
        self.trace.clear()

        self._gate(
            "instruction-set",
            lambda: verify(self.pinned_instructions,
                           InstructionManifest.from_files(instructions)),
        )
        self._gate(
            "intake",
            lambda: evaluate_startup(
                [InputSpec("prompt", True), InputSpec("run_id", False)], intake
            ),
        )

        writer = ConfinedWriter(self.scope_root)
        allowlist = PinnedEgressAllowlist(list(self.egress_allowlist))

        def effect() -> str:
            # Reached only when every earlier gate passed.
            self._gate("egress", lambda: allowlist.check(fetch_url))
            target = self._gate("write-scope", lambda: writer.resolve(write_path))
            return write_managed_block(target, content)

        gate = CapabilityGate(
            self.personas,
            {"write_guide": ToolSpec("write_guide", "repo.write", effect)},
        )

        # The three gates that wrap execution nest, which is how they compose in
        # practice: the objective authorizes the action, the budget charges for
        # it, and the capability gate admits the tool that performs it.
        document = self._gate(
            "objective",
            lambda: self.run.perform(
                action,
                lambda: self._gate(
                    "budget",
                    lambda: self.budget.run(
                        Charge("tool_calls", 1),
                        lambda: self._gate(
                            "capability",
                            lambda: gate.invoke("writer-agent", "write_guide"),
                        ),
                    ),
                ),
            ),
        )

        return Outcome(performed=True, gates=tuple(self.trace), document=document)

    def gates_run(self) -> tuple[str, ...]:
        return tuple(record.gate for record in self.trace)
