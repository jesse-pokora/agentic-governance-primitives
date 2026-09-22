"""Recorded demonstration of this app's atomic claim.

Runs the real CapabilityGate and writes demo.json. Regenerate the page with:

    python demo.py && python ../../demos/render.py .
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from capability_gate import CapabilityDenied, CapabilityGate, ToolSpec  # noqa: E402
from demo_trace import Trace, main  # noqa: E402


class SpyTool:
    def __init__(self, result):
        self.calls = 0
        self.result = result

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self.result


def build() -> Trace:
    read_repo = SpyTool("toy file contents")
    read_secrets = SpyTool("toy secret material")
    deploy = SpyTool("toy deploy receipt")

    personas = {"reviewer": {"repo.read"}, "release-agent": {"repo.read", "deploy.execute"}}
    tools = {
        "read_repo": ToolSpec("read_repo", "repo.read", read_repo),
        "read_secrets": ToolSpec("read_secrets", "repo.read_secrets", read_secrets),
        "deploy": ToolSpec("deploy", "deploy.execute", deploy),
    }
    gate = CapabilityGate(personas, tools)

    t = Trace(
        app="capability-gated-tool-invocation",
        claim=(
            "A tool call runs only if the calling persona's declared capability set "
            "contains that tool's exact required capability — and a denied call never "
            "enters the tool function at all."
        ),
        enforcement="deterministic",
        denial_type="CapabilityDenied",
    )

    t.allow(
        "reviewer holds repo.read, and read_repo requires it",
        {"persona": "reviewer", "tool": "read_repo", "requires": "repo.read"},
        lambda: gate.invoke("reviewer", "read_repo"),
        evidence=lambda: f"tool body entered {read_repo.calls} time",
    )
    t.deny(
        "reviewer does not hold deploy.execute",
        {"persona": "reviewer", "tool": "deploy", "requires": "deploy.execute"},
        lambda: gate.invoke("reviewer", "deploy"),
        evidence=lambda: f"tool body entered {deploy.calls} times",
        note="The count stays at zero: this is a gate, not an audit after the fact.",
    )
    t.deny(
        "a capability prefix does not imply the longer capability",
        {"persona": "reviewer", "holds": "repo.read", "tool": "read_secrets",
         "requires": "repo.read_secrets"},
        lambda: gate.invoke("reviewer", "read_secrets"),
        evidence=lambda: f"tool body entered {read_secrets.calls} times",
    )
    wildcard = CapabilityGate({"wildcard-persona": {"repo.*"}}, tools)
    t.deny(
        "a wildcard string grants nothing",
        {"persona": "wildcard-persona", "holds": "repo.*", "tool": "read_repo",
         "requires": "repo.read"},
        lambda: wildcard.invoke("wildcard-persona", "read_repo"),
        note="Reading structure into capability names would make every new tool "
             "name a silent policy change.",
    )
    personas["reviewer"].add("deploy.execute")
    t.deny(
        "mutating the source catalog after construction grants nothing",
        {"persona": "reviewer", "tool": "deploy", "attempt": "runtime escalation"},
        lambda: gate.invoke("reviewer", "deploy"),
        evidence=lambda: f"tool body entered {deploy.calls} times",
        note="The catalog captured at construction is the only authority.",
    )
    return t


if __name__ == "__main__":
    main(build, __file__)
