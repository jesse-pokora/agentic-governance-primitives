"""Single-purpose adversarial reviewer.

One function, schema-in/findings-out, callable with zero pipeline, zero
orchestrator, and no state carried between calls. The finding logic here
is a deterministic toy stand-in for what a real model call would do — the
governed part being demonstrated is the fixed input/output envelope and
statelessness, not the content-generation itself.
"""

from __future__ import annotations

ALLOWED_SEVERITIES = frozenset({"high", "medium", "low"})
_INPUT_FIELDS = frozenset({"artifact_id", "content"})
_OUTPUT_FIELDS = frozenset({"artifact_id", "findings"})
_FINDING_FIELDS = frozenset({"severity", "description"})


class InvalidReviewPayload(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _validate_input(payload: dict) -> None:
    if not isinstance(payload, dict) or set(payload.keys()) != _INPUT_FIELDS:
        raise InvalidReviewPayload("input_shape_mismatch")
    if not isinstance(payload["artifact_id"], str) or not isinstance(payload["content"], str):
        raise InvalidReviewPayload("input_field_type_mismatch")


def _validate_output(output: dict) -> None:
    assert set(output.keys()) == _OUTPUT_FIELDS
    for finding in output["findings"]:
        assert set(finding.keys()) == _FINDING_FIELDS
        assert finding["severity"] in ALLOWED_SEVERITIES


def review(payload: dict) -> dict:
    """Pure function: same payload in, same findings out, every time.

    No class, no module-level mutable state, no memory of any prior call.
    """
    _validate_input(payload)

    content = payload["content"]
    findings = []
    if "eval(" in content:
        findings.append(
            {"severity": "high", "description": "possible arbitrary code execution via eval()"}
        )
    if "password" in content.lower():
        findings.append(
            {"severity": "medium", "description": "hardcoded credential-like string detected"}
        )

    output = {"artifact_id": payload["artifact_id"], "findings": findings}
    _validate_output(output)
    return output
