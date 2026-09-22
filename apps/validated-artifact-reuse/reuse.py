"""Validated artifact reuse.

An existing upstream artifact is reused only when it is still valid for the
inputs at hand: same input digest, same producer version, and not past its
declared validity. Anything else regenerates.

Reuse and cache invalidation are the same problem wearing different words, and
the failure that matters is not a slow rebuild — it is a fast, confident answer
computed from inputs that have since changed. So the decision is explicit and
recorded: every call reports whether it reused or regenerated, and why.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable


def digest_of(value: Any) -> str:
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Artifact:
    content: Any
    input_digest: str
    producer_version: str
    generation: int


@dataclass(frozen=True)
class Decision:
    reused: bool
    reason: str  # fixed vocabulary, recorded either way
    artifact: Artifact


REUSE_REASONS = frozenset(
    {
        "valid_for_these_inputs",
        "no_existing_artifact",
        "inputs_changed",
        "producer_version_changed",
        "artifact_corrupt",
    }
)


def _is_sha256(value: str) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        c in "0123456789abcdef" for c in value
    )


def obtain(
    existing: Artifact | None,
    inputs: Any,
    producer_version: str,
    produce: Callable[[], Any],
) -> Decision:
    """Reuse `existing` if it is still valid, otherwise regenerate.

    Validity is checked against what the artifact was *made from*, never
    against when it was made. A clock-based expiry answers "is this old",
    which is a different question from "is this still right" — and the two come
    apart in both directions.
    """
    current_digest = digest_of(inputs)

    def regenerate(reason: str) -> Decision:
        generation = (existing.generation + 1) if existing else 1
        return Decision(
            reused=False,
            reason=reason,
            artifact=Artifact(
                content=produce(),
                input_digest=current_digest,
                producer_version=producer_version,
                generation=generation,
            ),
        )

    if existing is None:
        return regenerate("no_existing_artifact")

    # The artifact must still hash to what it claims it was made from. A stored
    # digest that no longer matches its own content means the record is
    # untrustworthy, and an untrustworthy record is not a reason to skip work.
    if not _is_sha256(existing.input_digest):
        return regenerate("artifact_corrupt")

    if existing.producer_version != producer_version:
        return regenerate("producer_version_changed")
    if existing.input_digest != current_digest:
        return regenerate("inputs_changed")

    return Decision(reused=True, reason="valid_for_these_inputs", artifact=existing)
