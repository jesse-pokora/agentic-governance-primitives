"""Staged input allowlist.

Only files matching a declared policy enter the agent's view, every excluded
file is recorded with a fixed-vocabulary reason, and the manifest lists exactly
what was staged. Exceeding a declared cap refuses the whole staging run rather
than quietly staging a prefix of it.

This is the input-side counterpart to write-scope confinement: that app governs
where an agent may write, this one governs what it may ever see.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field

EXCLUSION_REASONS = frozenset(
    {"suffix_not_allowed", "denied_name", "too_large", "symlink", "vcs_metadata"}
)


class StagingRefused(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class StagingPolicy:
    allowed_suffixes: frozenset[str]
    denied_names: frozenset[str]
    max_file_bytes: int
    max_files: int
    max_total_bytes: int


@dataclass
class StagingResult:
    staged: list[str] = field(default_factory=list)
    excluded: list[tuple[str, str]] = field(default_factory=list)

    @property
    def manifest(self) -> list[str]:
        """Exactly the staged set, in a fixed order."""
        return sorted(self.staged)


def _classify(source_root: str, rel: str, policy: StagingPolicy) -> str | None:
    """Return an exclusion reason, or None if the file may be staged."""
    absolute = os.path.join(source_root, rel)
    parts = rel.replace("\\", "/").split("/")

    if any(p in {".git", ".hg", ".svn"} for p in parts):
        return "vcs_metadata"
    if os.path.islink(absolute):
        # Not followed and not copied: a link is a path into somewhere the
        # policy never examined.
        return "symlink"
    if os.path.basename(rel) in policy.denied_names:
        return "denied_name"
    if os.path.splitext(rel)[1].lower() not in policy.allowed_suffixes:
        return "suffix_not_allowed"
    if os.path.getsize(absolute) > policy.max_file_bytes:
        return "too_large"
    return None


def stage(source_root: str, dest_root: str, policy: StagingPolicy) -> StagingResult:
    """Copy the admissible files into a fresh staging directory.

    Caps are checked against the admitted set *before* anything is copied, so
    an over-cap run stages nothing at all. Truncating to the cap instead would
    hand the agent a silently partial view of the repository — the worst of
    both outcomes, since nothing would look wrong.
    """
    result = StagingResult()

    for directory, _, files in os.walk(source_root):
        for name in sorted(files):
            rel = os.path.relpath(os.path.join(directory, name), source_root)
            reason = _classify(source_root, rel, policy)
            if reason:
                result.excluded.append((rel.replace("\\", "/"), reason))
            else:
                result.staged.append(rel.replace("\\", "/"))

    result.staged.sort()
    result.excluded.sort()

    if len(result.staged) > policy.max_files:
        raise StagingRefused("file_count_cap", f"{len(result.staged)} > {policy.max_files}")

    total = sum(os.path.getsize(os.path.join(source_root, p)) for p in result.staged)
    if total > policy.max_total_bytes:
        raise StagingRefused("total_byte_cap", f"{total} > {policy.max_total_bytes}")

    os.makedirs(dest_root, exist_ok=True)
    for rel in result.staged:
        target = os.path.join(dest_root, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(os.path.join(source_root, rel), target)

    return result
