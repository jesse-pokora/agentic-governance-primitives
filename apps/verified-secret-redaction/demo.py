"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from redaction import SecretRegistry  # noqa: E402

TOKEN = "toy-token-AAAA1111"
LONGER = "toy-token-AAAA1111-BBBB2222"
KEY = b"toy-correlation-key"


def build() -> Trace:
    registry = SecretRegistry([TOKEN], correlation_key=KEY)
    both = SecretRegistry([TOKEN, LONGER], correlation_key=KEY)

    t = Trace(
        app="verified-secret-redaction",
        claim=(
            "No registered secret can appear in an emitted artifact — the emitter "
            "redacts, then re-reads its own serialized output and refuses to emit if any "
            "secret survived."
        ),
        enforcement="deterministic",
        denial_type="RedactionFailure",
    )
    t.allow("a secret nested inside an artifact",
            {"artifact": '{"run": {"auth": {"token": "' + TOKEN + '"}}}'},
            lambda: registry.emit({"run": {"auth": {"token": TOKEN}}}),
            evidence=lambda: f"placeholder is stable: {registry.placeholder(TOKEN)}")
    t.allow("a secret embedded in a log line keeps its surroundings",
            {"line": f"GET /v1/toy Authorization: Bearer {TOKEN} -> 200"},
            lambda: registry.redact(f"GET /v1/toy Authorization: Bearer {TOKEN} -> 200"),
            evidence=lambda: "only the secret was replaced")
    t.allow("one secret containing another leaves no fragment",
            {"text": f"header {LONGER} footer", "registered": "both, longest first"},
            lambda: both.redact(f"header {LONGER} footer"),
            evidence=lambda: "no '-BBBB2222' tail survives",
            note="Replacing the shorter secret first would shred the longer one and "
                 "leave half of it in the output.")
    t.deny("output that reached the emitter already containing a secret",
           {"serialized": '{"leaked": "' + TOKEN + '"}', "check": "assert_clean()"},
           lambda: registry.assert_clean('{"leaked": "' + TOKEN + '"}'),
           evidence=lambda: "the failure names only the placeholder, never the secret",
           note="The emitter does not trust its own redactor; it re-reads the finished "
                "bytes.")
    return t


if __name__ == "__main__":
    main(build, __file__)
