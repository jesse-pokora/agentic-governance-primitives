"""Workspace attestation.

A governed run's *claimed* file changes are diffed against a real
git-worktree snapshot taken immediately before and after. A claim that
doesn't match the actual diff fails closed.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


class AttestationMismatch(Exception):
    def __init__(self, claimed: dict, actual: dict):
        super().__init__(f"attestation_mismatch: claimed={claimed} actual={actual}")
        self.claimed = claimed
        self.actual = actual


def _git(args: list[str], cwd: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return result.stdout


def init_snapshot_repo(repo_dir: str) -> None:
    """Initialize a git repo and commit its current contents — the 'before'
    snapshot every later diff is measured against.
    """
    _git(["init", "-q"], cwd=repo_dir)
    _git(["add", "-A"], cwd=repo_dir)
    _git(
        [
            "-c", "user.name=workspace-attestation-demo",
            "-c", "user.email=demo@example.invalid",
            "commit", "-q", "-m", "before-snapshot", "--allow-empty",
        ],
        cwd=repo_dir,
    )


@dataclass(frozen=True)
class WorkspaceDiff:
    added: frozenset[str]
    modified: frozenset[str]
    deleted: frozenset[str]

    def as_dict(self) -> dict:
        return {
            "added": sorted(self.added),
            "modified": sorted(self.modified),
            "deleted": sorted(self.deleted),
        }


def capture_actual_diff(repo_dir: str) -> WorkspaceDiff:
    """Diff the current working tree against the 'before' commit (HEAD)."""
    output = _git(["status", "--porcelain=v1"], cwd=repo_dir)
    added, modified, deleted = set(), set(), set()
    for line in output.splitlines():
        if not line:
            continue
        code, path = line[:2], line[3:]
        if code == "??":
            added.add(path)
        elif "D" in code:
            deleted.add(path)
        elif "M" in code or "A" in code:
            modified.add(path) if "M" in code else added.add(path)
        else:
            raise AttestationMismatch(
                claimed={}, actual={"unrecognized_status_code": code, "path": path}
            )
    return WorkspaceDiff(added=frozenset(added), modified=frozenset(modified), deleted=frozenset(deleted))


def attest(repo_dir: str, claimed_added: list[str], claimed_modified: list[str], claimed_deleted: list[str]) -> WorkspaceDiff:
    """Fail closed unless the claimed changes exactly match the real diff."""
    actual = capture_actual_diff(repo_dir)
    claimed = WorkspaceDiff(
        added=frozenset(claimed_added),
        modified=frozenset(claimed_modified),
        deleted=frozenset(claimed_deleted),
    )
    if claimed != actual:
        raise AttestationMismatch(claimed=claimed.as_dict(), actual=actual.as_dict())
    return actual
