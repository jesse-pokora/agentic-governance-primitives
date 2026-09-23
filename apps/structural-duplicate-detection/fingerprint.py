"""Structural duplicate detection.

Two functions with the same implementation shape produce the same fingerprint
regardless of their names, so a re-implementation under a new name is detected
exactly — no similarity score, no threshold.

This is the shape of an agent forgetting a dependency: it writes the function
that already exists, under a name it invented, and nothing notices because
nothing was looking for the *shape*. Names are the one part guaranteed to
differ, so the fingerprint discards them.

What this cannot do is stated in the README and is not a detail: a genuinely
different implementation of the same idea produces a different fingerprint and
is not reported. Catching that needs similarity scoring, which needs a
threshold, which is a number somebody picks — and this catalog does not pretend
a picked number is deterministic.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass


class SourceRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Fingerprinted:
    name: str
    line: int
    fingerprint: str


class _Normalizer(ast.NodeTransformer):
    """Rewrite a function into its shape: names become positional slots.

    Parameters and locals are renamed in order of first appearance, so
    `def a(x)` and `def b(y)` normalize identically. Docstrings are dropped.
    Literals are kept: two functions differing only in a constant are doing
    different things, and saying otherwise would make the fingerprint lie.
    """

    def __init__(self) -> None:
        self.slots: dict[str, str] = {}

    def _slot(self, name: str) -> str:
        if name not in self.slots:
            self.slots[name] = f"v{len(self.slots)}"
        return self.slots[name]

    def visit_arg(self, node: ast.arg) -> ast.arg:
        return ast.arg(arg=self._slot(node.arg), annotation=None)

    def visit_Name(self, node: ast.Name) -> ast.Name:
        # Only rename names bound inside the function. A call to an imported
        # helper keeps its name, because calling a different helper is a
        # different implementation.
        if node.id in self.slots:
            return ast.Name(id=self.slots[node.id], ctx=node.ctx)
        if isinstance(node.ctx, ast.Store):
            return ast.Name(id=self._slot(node.id), ctx=node.ctx)
        return node

    def visit_Expr(self, node: ast.Expr) -> ast.Expr | None:
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None  # a docstring or a bare string; not behaviour
        return self.generic_visit(node)


def fingerprint_function(node: ast.FunctionDef) -> str:
    """Hash the normalized shape of one function."""
    clone = ast.parse(ast.unparse(node)).body[0]
    clone.name = "f"
    clone.decorator_list = []
    normalized = _Normalizer().visit(clone)
    ast.fix_missing_locations(normalized)
    return hashlib.sha256(ast.unparse(normalized).encode("utf-8")).hexdigest()


def fingerprints(source: str) -> tuple[Fingerprinted, ...]:
    try:
        tree = ast.parse(source)
    except SyntaxError as err:
        raise SourceRejected("parse_error", str(err.msg)) from None

    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append(
                Fingerprinted(node.name, node.lineno, fingerprint_function(node))
            )
    return tuple(found)


def duplicates(*sources: str) -> tuple[tuple[Fingerprinted, ...], ...]:
    """Group functions sharing a fingerprint, across any number of sources.

    A group of one is not a duplicate and is not reported. Groups come back in
    a fixed order so two runs produce the same report.
    """
    if not sources:
        raise SourceRejected("no_sources", "nothing to compare")

    groups: dict[str, list[Fingerprinted]] = {}
    for source in sources:
        for item in fingerprints(source):
            groups.setdefault(item.fingerprint, []).append(item)

    return tuple(
        tuple(group)
        for _, group in sorted(groups.items())
        if len(group) > 1
    )
