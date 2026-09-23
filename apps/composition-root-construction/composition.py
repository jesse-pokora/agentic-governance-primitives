"""Composition-root construction.

A declared collaborator type may be constructed only inside the composition
root. Anywhere else it must arrive as a parameter.

This is dependency inversion stated so a machine can check it. "Use dependency
injection" is not checkable — it names a style. "These types are constructed in
exactly these functions" is, and it is what the style is for: one place that
knows how the system is wired, and everywhere else taking what it is given.

What counts as a collaborator is declared, not guessed. A checker that decided
for itself which calls look like collaborators would flag `Decimal("1.00")` and
be switched off by lunchtime.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass


class SourceRejected(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Construction:
    type_name: str
    line: int
    scope: str  # "<module>", "Class.method", or "function"


@dataclass(frozen=True)
class Policy:
    collaborators: frozenset[str]
    composition_root: frozenset[str]  # function names allowed to construct them

    @classmethod
    def of(cls, collaborators: set[str], composition_root: set[str]) -> Policy:
        if not collaborators:
            raise SourceRejected("no_collaborators_declared", "nothing to check")
        if not composition_root:
            # Without one, the rule is "never construct these", which is a
            # different and unsatisfiable instruction.
            raise SourceRejected("no_composition_root", "nowhere is allowed to wire")
        return cls(frozenset(collaborators), frozenset(composition_root))


class _Walker(ast.NodeVisitor):
    def __init__(self, collaborators: frozenset[str]):
        self.collaborators = collaborators
        self.found: list[Construction] = []
        self.mentioned = False
        self._scope: list[str] = ["<module>"]

    def _enter(self, name: str, node: ast.AST) -> None:
        self._scope.append(name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """A class body and a function body are both scopes for this purpose.

        These three were separate methods with identical bodies until the
        catalog's own structural-duplicate-detection was pointed at it.
        """
        self._enter(node.name, node)

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in self.collaborators:
            self.mentioned = True
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if name in self.collaborators:
            self.mentioned = True
            self.found.append(
                Construction(name, node.lineno, ".".join(self._scope[1:]) or "<module>")
            )
        self.generic_visit(node)


def constructions(source: str, policy: Policy) -> tuple[list[Construction], bool]:
    """Every construction of a declared collaborator, and whether any was named."""
    try:
        tree = ast.parse(source)
    except SyntaxError as err:
        raise SourceRejected("parse_error", str(err.msg)) from None

    walker = _Walker(policy.collaborators)
    walker.visit(tree)
    return walker.found, walker.mentioned


def check(source: str, policy: Policy) -> tuple[str, str]:
    """Return (verdict, detail): passed, failed, or not_applicable."""
    found, mentioned = constructions(source, policy)

    if not mentioned:
        # Nothing the instruction could apply to. Not the same as satisfying it.
        return "not_applicable", "no declared collaborator appears in this source"

    outside = [
        site for site in found
        if site.scope.split(".")[-1] not in policy.composition_root
    ]
    if outside:
        where = "; ".join(f"{s.type_name} at line {s.line} in {s.scope}" for s in outside)
        return "failed", where

    return "passed", f"{len(found)} construction(s), all in the composition root"
