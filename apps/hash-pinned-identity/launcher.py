"""Hash-pinned executable identity launcher.

A toy launcher that refuses to run any executable whose resolved absolute
path *and* SHA-256 don't both match a policy pinned outside the workspace —
even if the name on PATH is identical to a trusted one.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PinnedIdentity:
    absolute_path: str
    sha256: str


class IdentityMismatch(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def sha256_of_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class PinnedIdentityPolicy:
    """A policy pinned outside the workspace: name -> (absolute_path, sha256)."""

    def __init__(self, entries: dict[str, PinnedIdentity]):
        self._entries = dict(entries)

    def get(self, name: str) -> PinnedIdentity | None:
        return self._entries.get(name)


class HashPinnedLauncher:
    def __init__(self, policy: PinnedIdentityPolicy):
        self._policy = policy

    def launch(self, name: str, candidate_path: str) -> bytes:
        """Return the executable's bytes if it matches the pinned identity.

        Raises IdentityMismatch otherwise. Never falls back to "close enough".
        """
        pinned = self._policy.get(name)
        if pinned is None:
            raise IdentityMismatch(f"no pinned identity for name={name!r}")

        resolved = os.path.abspath(candidate_path)
        pinned_path = os.path.abspath(pinned.absolute_path)
        if resolved != pinned_path:
            raise IdentityMismatch(
                f"path_mismatch: name={name!r} resolved={resolved!r} "
                f"pinned={pinned_path!r}"
            )

        if not os.path.isfile(resolved):
            raise IdentityMismatch(f"missing_file: {resolved!r}")

        actual_hash = sha256_of_file(resolved)
        if actual_hash != pinned.sha256:
            raise IdentityMismatch(
                f"hash_mismatch: name={name!r} path={resolved!r} "
                f"expected={pinned.sha256} actual={actual_hash}"
            )

        with open(resolved, "rb") as f:
            return f.read()
