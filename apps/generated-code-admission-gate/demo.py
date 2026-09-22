"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from admission_gate import AdmissionPolicy, admit_and_run  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

POLICY = AdmissionPolicy.of(imports={"math"}, calls={"record", "len", "math.sqrt"})


class Spy:
    def __init__(self):
        self.calls = []

    def __call__(self, value):
        self.calls.append(value)
        return value


def build() -> Trace:
    spy = Spy()
    def run(src, policy=POLICY):
        # Return a named value rather than the whole namespace: the namespace
        # holds the live spy object, whose repr carries a memory address and
        # would make every recording differ from the last.
        ns = admit_and_run(src, policy, {"record": spy})
        return {k: v for k, v in ns.items() if k != "record"}

    policy_text = "imports: math | calls: record, len, math.sqrt"

    t = Trace(
        app="generated-code-admission-gate",
        claim=(
            "Model-generated code is admitted only if every import, call, and attribute "
            "access in its parsed AST is permitted by the declared policy — a denied "
            "program is never compiled and never runs."
        ),
        enforcement="deterministic",
        denial_type="AdmissionDenied",
    )
    t.allow("generated code using only permitted names",
            {"source": "total = len([1, 2, 3])\nrecord(total)", "policy": policy_text},
            lambda: run("total = len([1, 2, 3])\nrecord(total)\n"),
            evidence=lambda: f"record() entered {len(spy.calls)} time")
    t.deny("an undeclared import, two lines after a permitted call",
           {"source": "record('side effect')\nimport os", "policy": policy_text},
           lambda: run("record('side effect')\nimport os\n"),
           evidence=lambda: f"record() entered {len(spy.calls)} time — unchanged",
           note="Admission is whole-program. Line 1 does not run because line 2 is "
                "inadmissible.")
    t.deny("the dunder import bypass",
           {"source": "os = __import__('os')", "policy": policy_text},
           lambda: run("os = __import__('os')\n"),
           note="A denylist matching the word 'import' at line start misses this "
                "entirely.")
    t.deny("the class-hierarchy escape, which imports nothing at all",
           {"source": "leaked = ().__class__.__bases__[0].__subclasses__()"},
           lambda: run("leaked = ().__class__.__bases__[0].__subclasses__()\n"),
           note="Reaches every loaded class without an import. Dunder access is "
                "refused as a shape.")
    t.deny("eval, against a policy that explicitly allowlists eval",
           {"source": "record(eval('1+1'))", "policy": "calls: eval, record"},
           lambda: run("record(eval('1+1'))\n",
                       AdmissionPolicy.of(imports=set(), calls={"eval", "record"})),
           note="A policy that could re-enable the escape hatches would be a policy "
                "that can disable itself.")
    t.allow("a forbidden name inside a string is not a call",
            {"source": 'banner = "import os and eval() are not allowed"\nrecord(banner)'},
            lambda: run('banner = "import os and eval() are not allowed"\nrecord(banner)\n'),
            evidence=lambda: f"record() entered {len(spy.calls)} times total",
            note="This is the step that separates parsing from pattern matching: a "
                 "denylist rejects this admissible program.")
    return t


if __name__ == "__main__":
    main(build, __file__)
