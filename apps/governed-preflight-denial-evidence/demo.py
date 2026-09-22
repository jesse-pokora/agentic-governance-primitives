"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from preflight import ALLOWED_FIELDS, run_preflight  # noqa: E402


def build() -> Trace:
    t = Trace(
        app="governed-preflight-denial-evidence",
        claim=(
            "When a precondition fails, the system emits a fixed-shape, allowlisted-field "
            "denial record — never raw stderr, paths, or secrets."
        ),
        enforcement="deterministic",
        denial_type="n/a — this app emits a denial record, it does not raise",
    )

    def passing():
        return None

    def leaky():
        raise RuntimeError(
            "connect failed: token=toy-secret-AAAA1111 at /home/toy/.ssh/id_rsa"
        )

    t.allow("a precondition that holds emits no record at all",
            {"precondition": "credentials_present", "result": "passed"},
            lambda: run_preflight("credentials_present", passing) or "None — nothing to report",
            evidence=lambda: "silence on success; a record means something failed")
    t.verdict("a precondition that fails with a secret-bearing exception",
              {"precondition": "credentials_present",
               "raised": "token=toy-secret-AAAA1111 at /home/toy/.ssh/id_rsa"},
              lambda: run_preflight("credentials_present", leaky),
              lambda rec: False,
              lambda rec: f"denied={rec.to_dict()['denied']} "
                          f"reason_code={rec.to_dict()['reason_code']}",
              evidence=lambda: f"fields emitted: {sorted(ALLOWED_FIELDS)}",
              note="The exception text is where secrets leak into audit logs. The "
                   "record's shape is fixed in advance, so there is nowhere for it to go.")
    t.verdict("the emitted record carries no field outside the allowlist",
              {"check": "set(record) - ALLOWED_FIELDS"},
              lambda: set(run_preflight("credentials_present", leaky).to_dict()) - ALLOWED_FIELDS,
              lambda extra: not extra,
              lambda extra: "no fields outside the allowlist" if not extra else str(extra),
              note="An allowlist of fields, rather than a denylist of secrets, is what "
                   "makes this checkable without knowing every secret in advance.")
    return t


if __name__ == "__main__":
    main(build, __file__)
