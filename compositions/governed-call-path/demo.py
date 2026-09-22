"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from pipeline import (  # noqa: E402
    GATES,
    Action,
    GovernedCallPath,
    InstructionManifest,
    PinnedInstructionSet,
)

AGENTS_MD = b"# toy agent instructions\nalways state the atomic claim\n"
INSTRUCTIONS = {"AGENTS.md": AGENTS_MD}
INTAKE = {"prompt": "summarize svc-fake-a"}
ACTION = Action("write_guide", ("summarize-repository",))
URL = "https://api.example.test/v1/toy"


def build() -> Trace:
    tmp = tempfile.mkdtemp(prefix="demo-gcp-")
    scope = os.path.join(tmp, "work")
    os.makedirs(scope)

    def fresh(**overrides):
        path = GovernedCallPath(
            pinned_instructions=PinnedInstructionSet.pin(
                InstructionManifest.from_files(INSTRUCTIONS)
            ),
            objectives={"summarize-repository"},
            personas=overrides.get("personas", {"writer-agent": {"repo.write"}}),
            egress_allowlist=["https://api.example.test"],
            scope_root=scope,
            limits=overrides.get("limits", {"tool_calls": 4}),
        )
        return path

    def request(path, **overrides):
        return path.handle(
            intake=overrides.get("intake", INTAKE),
            instructions=overrides.get("instructions", dict(INSTRUCTIONS)),
            action=overrides.get("action", ACTION),
            fetch_url=overrides.get("fetch_url", URL),
            write_path=overrides.get("write_path", "AGENTS.md"),
            content="generated guide",
        )

    t = Trace(
        app="governed-call-path",
        claim=(
            "One request passes through every declared gate in a fixed order, and the "
            "first gate that refuses stops it — no later gate is entered, no effect "
            "occurs, and the ledger records which gate refused."
        ),
        enforcement="composition",
        denial_type="RequestRefused",
        redactions={tmp: "<tmp>", tmp.replace("\\", "/"): "<tmp>"},
    )

    ok = fresh()
    t.allow(
        "a request that satisfies every gate",
        {"gates": " -> ".join(GATES), "intake": "prompt", "objective":
         "summarize-repository", "url": URL, "write": "AGENTS.md"},
        lambda: [r.gate for r in request(ok).gates],
        evidence=lambda: f"ledger entries: {len(ok.ledger.entries)}; verifies: "
                         f"{ok.ledger.verify().valid}",
        note="Seven gates, one effect. There is no router and no loop — the order "
             "is a constant.",
    )

    drifted = fresh()
    t.deny(
        "the instruction set drifted since it was pinned",
        {"stops at": "instruction-set (gate 1 of 7)"},
        lambda: request(drifted, instructions={"AGENTS.md": AGENTS_MD.replace(b"always", b"rarely")}),
        evidence=lambda: f"gates entered: {list(drifted.gates_run())}",
        note="Nothing after gate 1 is even entered.",
    )

    no_objective = fresh()
    t.deny(
        "the action serves a goal nobody declared",
        {"stops at": "objective (gate 3 of 7)", "serves": "ship-it"},
        lambda: request(no_objective, action=Action("write_guide", ("ship-it",))),
        evidence=lambda: f"gates entered: {list(no_objective.gates_run())}",
    )

    no_capability = fresh(personas={"writer-agent": {"repo.read"}})
    t.deny(
        "the persona may read but not write",
        {"stops at": "capability (gate 5 of 7)", "holds": "repo.read",
         "requires": "repo.write"},
        lambda: request(no_capability),
        evidence=lambda: f"gates entered: {list(no_capability.gates_run())}",
    )

    bad_egress = fresh()
    t.deny(
        "the tool tries to reach an unlisted host",
        {"stops at": "egress (gate 6 of 7)", "url": "https://exfil.evil.test/collect"},
        lambda: request(bad_egress, fetch_url="https://exfil.evil.test/collect"),
        evidence=lambda: f"gates entered: {list(bad_egress.gates_run())}; file written: "
                         f"{os.path.exists(os.path.join(scope, 'AGENTS.md'))}",
        note="Five gates passed and the sixth refused, so the write never happened. "
             "Passing most of the gates is not passing.",
    )

    recorded = fresh()
    try:
        request(recorded, fetch_url="https://exfil.evil.test/collect")
    except Exception:
        pass
    t.allow(
        "what the ledger holds after that refusal",
        {"run": "refused at egress"},
        lambda: [
            f"{e.payload['gate']}: {e.payload['verdict']}" for e in recorded.ledger.entries
        ],
        evidence=lambda: f"tamper-evident: {recorded.ledger.verify().valid}",
        note="A gate that logged only what it allowed would be useless exactly when "
             "it mattered.",
    )
    return t


if __name__ == "__main__":
    main(build, __file__)
