"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from diagnostics import MAX_INSPECTED_BYTES, persist_failure  # noqa: E402

SECRETY = (b"Traceback: connecting with token=toy-secret-AAAA1111\n"
           b"Permission denied opening /home/toy/.ssh/id_rsa\n")


def build() -> Trace:
    t = Trace(
        app="safe-failure-diagnostics",
        claim=(
            "A child-process failure is classified into one of a fixed vocabulary of "
            "categories from at most 8,192 observed bytes, and only the category — never "
            "the bytes — is ever persisted."
        ),
        enforcement="deterministic",
        denial_type="n/a — this app persists a category, it does not raise",
    )
    for label, raw in (
        ("a timeout", b"error: operation timed out after 30s\n"),
        ("a permissions failure", b"sh: cannot open file: Permission denied\n"),
        ("output matching no known marker", b"\x00\x01 gibberish \xff\n"),
    ):
        t.allow(f"{label} is classified from its output",
                {"raw output": raw.decode("utf-8", "replace").strip()[:70]},
                lambda raw=raw: persist_failure(raw),
                evidence=lambda: "the record holds a category, not the bytes")

    t.allow("output carrying a token and a private key path",
            {"raw output": "token=toy-secret-AAAA1111 ... /home/toy/.ssh/id_rsa"},
            lambda: persist_failure(SECRETY),
            evidence=lambda: "neither the token nor the path appears in what is kept",
            note="Raw stderr is where secrets leak into audit logs. The category is "
                 "the only thing that survives.")

    huge = b"x" * (MAX_INSPECTED_BYTES * 4) + b"\nPermission denied\n"
    t.allow("output far larger than the inspection bound",
            {"raw output": f"{len(huge)} bytes", "inspected": f"{MAX_INSPECTED_BYTES} bytes"},
            lambda: persist_failure(huge),
            evidence=lambda: "classification reads a bounded prefix, so a huge failure "
                             "cannot exhaust the classifier",
            note="The marker past the bound is not found — a bound that is honest "
                 "about what it did not read.")
    return t


if __name__ == "__main__":
    main(build, __file__)
