"""Hash-pinned instruction set.

A run pins the exact SHA-256 of every instruction file in effect. A later run
whose instruction set differs by a single byte — or by one file added or
removed — fails closed rather than executing under drifted instructions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable


class InstructionDrift(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def sha256_of_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class InstructionManifest:
    """Every instruction file in effect, as (logical_name, sha256) pairs.

    Built from a name -> bytes mapping, so the manifest binds each hash to the
    name it was loaded under. Two files that swap contents produce a different
    manifest even though the multiset of hashes is unchanged.
    """

    entries: tuple[tuple[str, str], ...]

    @classmethod
    def from_files(cls, files: dict[str, bytes]) -> InstructionManifest:
        return cls(
            tuple(sorted((name, sha256_of_bytes(data)) for name, data in files.items()))
        )

    @property
    def digest(self) -> str:
        """One digest over the whole set, independent of insertion order."""
        return sha256_of_bytes(canonical_json(dict(self.entries)).encode("utf-8"))

    def as_dict(self) -> dict[str, str]:
        return dict(self.entries)


@dataclass(frozen=True)
class PinnedInstructionSet:
    """What a run recorded about the instructions it executed under."""

    manifest_digest: str
    per_file: tuple[tuple[str, str], ...]

    @classmethod
    def pin(cls, manifest: InstructionManifest) -> PinnedInstructionSet:
        return cls(manifest_digest=manifest.digest, per_file=manifest.entries)


def verify(pinned: PinnedInstructionSet, current: InstructionManifest) -> None:
    """Raise InstructionDrift unless `current` is the pinned instruction set.

    Reasons are reported in a fixed precedence — removed, then added, then
    changed — and name the lexicographically first offending file, so the same
    pair of manifests always yields the same reason and detail.
    """
    if current.digest == pinned.manifest_digest:
        return

    pinned_files = dict(pinned.per_file)
    current_files = current.as_dict()

    removed = sorted(set(pinned_files) - set(current_files))
    if removed:
        raise InstructionDrift("instruction_removed", removed[0])

    added = sorted(set(current_files) - set(pinned_files))
    if added:
        raise InstructionDrift("instruction_added", added[0])

    changed = sorted(
        name for name, digest in pinned_files.items() if current_files[name] != digest
    )
    if changed:
        raise InstructionDrift(
            "content_drift",
            f"{changed[0]} pinned={pinned_files[changed[0]]} "
            f"actual={current_files[changed[0]]}",
        )

    # Same names, same per-file hashes, different manifest digest: the pin
    # itself is inconsistent. Fail closed rather than guessing which to trust.
    raise InstructionDrift("manifest_digest_mismatch", pinned.manifest_digest)


def run_under(
    pinned: PinnedInstructionSet,
    current: InstructionManifest,
    action: Callable[[], Any],
) -> Any:
    """Run `action` only if the current instruction set is the pinned one."""
    verify(pinned, current)
    return action()
