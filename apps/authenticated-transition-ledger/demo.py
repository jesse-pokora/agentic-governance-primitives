"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from ledger import AuthenticatedTransitionLedger, canonical_json  # noqa: E402
import hashlib  # noqa: E402


def build() -> Trace:
    ledger = AuthenticatedTransitionLedger(secret_key=b"toy-shared-secret")
    for payload in (
        {"actor": "agent-1", "action": "provision", "target": "svc-fake-a"},
        {"actor": "agent-2", "action": "deploy", "target": "svc-fake-b"},
        {"actor": "agent-1", "action": "rollback", "target": "svc-fake-a"},
    ):
        ledger.append(payload)

    t = Trace(
        app="authenticated-transition-ledger",
        claim=(
            "An append-only, SHA-256-chained, HMAC-signed event log detects a single "
            "edited byte anywhere in its history, not just at the tampered row."
        ),
        enforcement="deterministic",
        denial_type="VerificationResult(valid=False)",
    )
    ok = lambda r: r.valid  # noqa: E731
    say = lambda r: f"{r.reason} at entry {r.first_bad_index}" if not r.valid else "chain intact"  # noqa: E731

    t.verdict("three appended entries, nothing touched",
              {"entries": 3, "check": "verify()"},
              ledger.verify, ok, say,
              evidence=lambda: "every link, hash and signature recomputed from genesis")

    ledger.entries[0].payload["target"] = "svc-fake-a-TAMPERED"
    t.verdict("one byte edited in entry 0, the oldest row",
              {"edited": "entries[0].payload.target", "check": "verify()"},
              ledger.verify, ok, say,
              evidence=lambda: "detected at entry 0, not merely at the tail",
              note="Verification walks the whole chain, so age is no protection.")

    entry = ledger.entries[1]
    entry.payload["action"] = "delete"
    entry.entry_hash = hashlib.sha256(
        (entry.prev_hash + canonical_json(entry.payload)).encode("utf-8")
    ).hexdigest()
    ledger.entries[0].payload["target"] = "svc-fake-a"  # undo the first tamper
    t.verdict("a careful attacker recomputes the hash but cannot forge the HMAC",
              {"edited": "entries[1].payload.action", "entry_hash": "recomputed to match"},
              ledger.verify, ok, say,
              evidence=lambda: "hash check passes; signature check does not",
              note="Recomputing the hash is free. Signing it requires the secret.")
    return t


if __name__ == "__main__":
    main(build, __file__)
