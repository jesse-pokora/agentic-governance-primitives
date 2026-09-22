"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from contract_check import verify_request_contract  # noqa: E402
from demo_trace import Trace, main  # noqa: E402

CONTRACT = {"provider": "toy-bedrock", "model_id": "toy-embed-v2",
            "version": "2026-01-01", "dimensions": 1024}


def build() -> Trace:
    t = Trace(
        app="deterministic-embedding-contract-check",
        claim=(
            "An embedding call's provider, model ID, version, and dimensions can be "
            "verified byte-for-byte against a captured request — with no live AWS call."
        ),
        enforcement="deterministic",
        denial_type="ContractMismatch",
    )
    t.allow("a captured request matching the contract in every field",
            dict(CONTRACT),
            lambda: verify_request_contract(dict(CONTRACT), CONTRACT) or "contract holds",
            evidence=lambda: "a pure dict comparison — the module makes no network "
                             "imports at all")
    t.deny("a silently upgraded model id",
           dict(CONTRACT, model_id="toy-embed-v3"),
           lambda: verify_request_contract(dict(CONTRACT, model_id="toy-embed-v3"), CONTRACT),
           note="The call still succeeds against the provider. The vectors it returns "
                "are simply not the ones the index was built with.")
    t.deny("a dimension count that no longer matches the index",
           dict(CONTRACT, dimensions=1536),
           lambda: verify_request_contract(dict(CONTRACT, dimensions=1536), CONTRACT))
    t.deny("several fields drifting at once",
           dict(CONTRACT, provider="other-provider", version="2026-06-01"),
           lambda: verify_request_contract(
               dict(CONTRACT, provider="other-provider", version="2026-06-01"), CONTRACT),
           evidence=lambda: "every mismatched field is listed, not just the first",
           note="Reporting one field at a time turns one fix into several rounds.")
    return t


if __name__ == "__main__":
    main(build, __file__)
