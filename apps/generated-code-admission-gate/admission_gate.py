"""Generated-code admission gate.

Model-generated code is parsed and checked against a declared policy *before*
it is compiled or executed. Every import, every call, and every attribute
access in the parsed AST must be permitted, or the program is rejected and
never runs.

READ THIS FIRST — this is an admission gate, NOT a sandbox. It decides whether
code is allowed to start. It does not contain code that is already running.
Restricted-namespace `exec` in CPython is known to be escapable, and this
module makes no claim otherwise; real isolation needs a process, container, or
VM boundary. What is claimed here, and tested, is that a denied program never
reaches `compile`.
"""

from __future__ import annotations

import ast
import builtins
from dataclasses import dataclass


class AdmissionDenied(Exception):
    def __init__(self, reason: str, detail: str = "", lineno: int | None = None):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail
        self.lineno = lineno


# Names a policy may not allowlist. These are the escape hatches: each one
# turns a static check of the source into a check of source that no longer
# describes what will run. A policy that could re-enable them would be a
# policy that can disable itself.
FORBIDDEN_NAMES = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
    }
)


def is_dunder(name: str) -> bool:
    """Dunder access is the standard route out of a restricted namespace.

    `().__class__.__bases__[0].__subclasses__()` reaches every loaded class
    without importing anything, so the gate refuses dunder names outright
    rather than trying to enumerate which ones are dangerous.
    """
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


@dataclass(frozen=True)
class AdmissionPolicy:
    allowed_imports: frozenset[str]
    allowed_calls: frozenset[str]

    @classmethod
    def of(cls, imports: set[str], calls: set[str]) -> AdmissionPolicy:
        return cls(allowed_imports=frozenset(imports), allowed_calls=frozenset(calls))


# When two violations land on the same source position — `__import__('os')` is
# both a forbidden name and a disallowed call — the more specific reason wins,
# so one program always yields one reason.
SEVERITY = {
    "forbidden_name": 0,
    "dunder_access": 1,
    "import_not_allowed": 2,
    "call_not_allowed": 3,
    "unresolvable_call": 4,
}


@dataclass(frozen=True)
class Violation:
    reason: str
    detail: str
    lineno: int
    col: int


def _dotted_name(node: ast.AST) -> str | None:
    """Resolve `a.b.c` to "a.b.c"; return None for anything more dynamic."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def find_violations(tree: ast.AST, policy: AdmissionPolicy) -> list[Violation]:
    violations: list[Violation] = []

    def add(node: ast.AST, reason: str, detail: str) -> None:
        violations.append(
            Violation(
                reason=reason,
                detail=detail,
                lineno=getattr(node, "lineno", 0),
                col=getattr(node, "col_offset", 0),
            )
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in policy.allowed_imports:
                    add(node, "import_not_allowed", alias.name)

        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in policy.allowed_imports:
                add(node, "import_not_allowed", node.module or "<relative>")

        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES:
                add(node, "forbidden_name", node.id)
            elif is_dunder(node.id):
                add(node, "dunder_access", node.id)

        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_NAMES:
                add(node, "forbidden_name", node.attr)
            elif is_dunder(node.attr):
                add(node, "dunder_access", node.attr)

        elif isinstance(node, ast.Call):
            name = _dotted_name(node.func)
            if name is None:
                # A call on something that is not a plain dotted name — a
                # subscript, a lambda, a returned object. The gate cannot say
                # statically what it calls, so it does not admit it.
                add(node, "unresolvable_call", ast.dump(node.func)[:60])
            elif name not in policy.allowed_calls:
                add(node, "call_not_allowed", name)

    return violations


def inspect_source(source: str, policy: AdmissionPolicy) -> ast.AST:
    """Parse and check. Raises AdmissionDenied; never compiles or runs.

    All violations are collected and the earliest in source order is reported,
    so the same program always produces the same denial.
    """
    try:
        tree = ast.parse(source, filename="<generated>", mode="exec")
    except SyntaxError as err:
        raise AdmissionDenied("parse_error", str(err.msg), err.lineno) from None

    violations = find_violations(tree, policy)
    if violations:
        first = min(violations, key=lambda v: (v.lineno, v.col, SEVERITY[v.reason]))
        raise AdmissionDenied(first.reason, first.detail, first.lineno)

    return tree


def _guarded_import(policy: AdmissionPolicy):
    real_import = builtins.__import__

    def guarded(name, globals=None, locals=None, fromlist=(), level=0):
        root = name.split(".")[0]
        if root not in policy.allowed_imports:
            raise AdmissionDenied("import_not_allowed", name)
        return real_import(name, globals, locals, fromlist, level)

    return guarded


def admit_and_run(
    source: str, policy: AdmissionPolicy, namespace: dict | None = None
) -> dict:
    """Admit the source, then execute it in a restricted namespace.

    Admission happens first and raises, so a denied program is never compiled.
    The restricted namespace narrows what admitted code can reach; it is a
    second layer, not a boundary. See the module docstring.
    """
    tree = inspect_source(source, policy)

    exposed = {
        name: getattr(builtins, name)
        for name in policy.allowed_calls
        if hasattr(builtins, name) and name not in FORBIDDEN_NAMES
    }
    # An admitted `import math` still needs a real importer at runtime. The one
    # supplied here honours the same allowlist the static pass used, so the
    # runtime cannot import what the gate would not have admitted. The source
    # calling `__import__` by name is still refused statically.
    exposed["__import__"] = _guarded_import(policy)
    environment: dict = {"__builtins__": exposed}
    environment.update(namespace or {})

    exec(compile(tree, filename="<generated>", mode="exec"), environment)
    return {k: v for k, v in environment.items() if not k.startswith("__")}
