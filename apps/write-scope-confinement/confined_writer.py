"""Write-scope confinement.

A write is denied before any bytes touch disk unless its fully resolved path
lies inside a declared scope root. Parent-directory traversal, absolute-path
substitution, a sibling directory that merely shares a name prefix, and a
symlink inside the scope pointing outside it all fail closed.
"""

from __future__ import annotations

import os


class WriteDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def _same_path(a: str, b: str) -> bool:
    return os.path.normcase(a) == os.path.normcase(b)


def _is_inside(root: str, candidate: str) -> bool:
    """True if `candidate` is strictly inside `root`.

    Compares path *components* via commonpath rather than string prefixes:
    "/work/repo-evil" starts with "/work/repo" as a string but is a different
    directory.
    """
    root_n = os.path.normcase(root)
    candidate_n = os.path.normcase(candidate)
    try:
        return os.path.commonpath([root_n, candidate_n]) == root_n and not _same_path(
            root, candidate
        )
    except ValueError:
        # Different drives or mixed absolute/relative: not inside, by definition.
        return False


class ConfinedWriter:
    """Mediates writes against one declared scope root."""

    def __init__(self, scope_root: str):
        root = os.path.realpath(scope_root)
        if not os.path.isdir(root):
            raise ValueError(f"scope root is not an existing directory: {scope_root!r}")
        self._root = root

    @property
    def scope_root(self) -> str:
        return self._root

    def resolve(self, path: str) -> str:
        """Return the absolute path a write would land on, or raise.

        Distinguishes three ways out of the scope by comparing the path before
        symlink resolution with the path after it:

        - the requested path is already outside  -> traversal_escape / outside_scope
        - it looks inside but resolves outside   -> symlink_escape
        """
        if not path or not path.strip():
            raise WriteDenied("invalid_path", "empty path")

        joined = path if os.path.isabs(path) else os.path.join(self._root, path)
        lexical = os.path.abspath(joined)  # normalizes ".." without touching disk
        resolved = os.path.realpath(joined)  # follows symlinks in existing ancestors

        if _same_path(lexical, self._root):
            raise WriteDenied("invalid_path", f"is the scope root: {self._root}")

        if not _is_inside(self._root, lexical):
            components = path.replace("\\", "/").split("/")
            reason = "traversal_escape" if os.pardir in components else "outside_scope"
            raise WriteDenied(reason, lexical)

        if not _is_inside(self._root, resolved):
            raise WriteDenied("symlink_escape", f"{lexical} -> {resolved}")

        if os.path.isdir(resolved):
            raise WriteDenied("invalid_path", f"is a directory: {resolved}")

        return resolved

    def write(self, path: str, data: bytes) -> str:
        """Write `data` to `path`, or raise before creating anything at all.

        Resolution happens first, so a denied write leaves no file, no partial
        file, and no freshly created parent directories behind.
        """
        target = self.resolve(path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as f:
            f.write(data)
        return target
