"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from catalog import audit_catalog, capabilities_of  # noqa: E402
from demo_trace import Trace, main  # noqa: E402
from runtime import RuntimeProcessList  # noqa: E402


def build() -> Trace:
    catalog = audit_catalog()
    personas = sorted(catalog["personas"])
    runtime = RuntimeProcessList()
    runtime.register(4242, personas[0], "2026-09-22T06:00:00Z")

    t = Trace(
        app="persona-capability-catalog",
        claim=(
            "\"Who is allowed to do what\" (a YAML+JSON-Schema catalog) is fully separate "
            "from \"what's running right now\" (a runtime process list) — you can audit "
            "the first without touching the second."
        ),
        enforcement="informational",
        denial_type="n/a — this app is a catalog, it denies nothing",
    )
    t.allow("auditing the declared catalog",
            {"source": "catalog.yaml", "validated against": "schema.json"},
            lambda: ", ".join(personas),
            evidence=lambda: f"{len(personas)} personas declared, schema-valid",
            note="This app is classed informational for a reason: it declares "
                 "authority and enforces none. The enforcement half is "
                 "capability-gated-tool-invocation.")
    t.allow("reading one persona's declared capabilities",
            {"persona": personas[0]},
            lambda: ", ".join(capabilities_of(catalog, personas[0])),
            evidence=lambda: "answered entirely from the catalog; nothing was started")
    t.allow("what is actually running right now",
            {"call": "list_running()"},
            lambda: [f"pid {p.pid} as {p.persona_name}" for p in runtime.list_running()],
            evidence=lambda: "a separate structure with a separate lifetime")
    t.verdict("a persona that is declared but not running",
              {"persona": personas[-1], "declared": "yes"},
              lambda: runtime.is_running(personas[-1]),
              lambda running: not running,
              lambda running: "running" if running else "declared, not running",
              note="Declared and running are different questions. Conflating them is "
                   "how a catalog becomes a description of the past.")
    return t


if __name__ == "__main__":
    main(build, __file__)
