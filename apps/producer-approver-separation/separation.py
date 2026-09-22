"""Producer/approver separation.

Whoever produced an artifact cannot approve it, and an approval names the exact
artifact digest it covers. Both halves are needed: separation without binding
lets an approval drift onto a later artifact, and binding without separation
lets the producer sign its own work.

Identity is compared after normalization, because "toy-agent" and
"Toy-Agent  " are the same actor wearing different spellings, and an
independence check that a rename defeats is decorative.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


class ApprovalDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def digest_of(artifact: Any) -> str:
    serialized = json.dumps(artifact, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_actor(name: str) -> str:
    return " ".join(name.strip().casefold().split())


@dataclass(frozen=True)
class Artifact:
    produced_by: str
    content: Any

    @property
    def digest(self) -> str:
        return digest_of(self.content)


@dataclass(frozen=True)
class Approval:
    approved_by: str
    artifact_digest: str


@dataclass(frozen=True)
class AcceptedArtifact:
    digest: str
    produced_by: str
    approved_by: str


def accept(artifact: Artifact, approval: Approval, delegates: dict[str, str] | None = None) -> AcceptedArtifact:
    """Accept an artifact, or refuse.

    `delegates` maps an actor to the principal it acts for. A producer that
    approves through a delegate is still the producer: separation that any
    service account defeats is not separation.
    """
    delegates = {normalize_actor(k): normalize_actor(v) for k, v in (delegates or {}).items()}

    def principal(name: str) -> str:
        actor = normalize_actor(name)
        return delegates.get(actor, actor)

    if not normalize_actor(artifact.produced_by):
        raise ApprovalDenied("unattributed_artifact", "producer is unnamed")
    if not normalize_actor(approval.approved_by):
        raise ApprovalDenied("unattributed_approval", "approver is unnamed")

    if principal(approval.approved_by) == principal(artifact.produced_by):
        raise ApprovalDenied(
            "self_approval",
            f"{normalize_actor(approval.approved_by)} produced this artifact",
        )

    if approval.artifact_digest != artifact.digest:
        raise ApprovalDenied(
            "approval_not_bound",
            f"approves={approval.artifact_digest[:16]}... artifact={artifact.digest[:16]}...",
        )

    return AcceptedArtifact(
        digest=artifact.digest,
        produced_by=normalize_actor(artifact.produced_by),
        approved_by=normalize_actor(approval.approved_by),
    )
