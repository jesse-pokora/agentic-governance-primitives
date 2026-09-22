"""Reduced child environment.

A child process receives only the variables a declared policy passes through.
Everything else in the parent's environment — including every secret seeded
into it — is absent, not redacted, because a variable that is not there cannot
be read by anything the child runs.

The default direction matters more than the list. An allowlist is wrong only
when it omits something the child needed, and that failure is loud. A denylist
is wrong whenever anyone adds a new secret, and that failure is silent.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


class EnvironmentDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


# Variables a process needs to start at all on the host platforms. Passing
# these through is a decision, recorded here rather than left implicit.
PLATFORM_ESSENTIALS = frozenset(
    {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR", "HOME", "LANG"}
)


@dataclass(frozen=True)
class EnvironmentPolicy:
    passthrough: frozenset[str]
    injected: tuple[tuple[str, str], ...] = ()
    include_platform_essentials: bool = True

    @classmethod
    def of(cls, passthrough: set[str], injected: dict[str, str] | None = None,
           include_platform_essentials: bool = True) -> EnvironmentPolicy:
        return cls(
            passthrough=frozenset(passthrough),
            injected=tuple(sorted((injected or {}).items())),
            include_platform_essentials=include_platform_essentials,
        )


def build_child_environment(parent: dict[str, str], policy: EnvironmentPolicy) -> dict[str, str]:
    """Return the child's whole environment, built up rather than filtered down.

    Starting from {} and adding is what makes the guarantee hold for variables
    nobody anticipated. Starting from the parent and deleting only ever removes
    what somebody already thought of.
    """
    allowed = set(policy.passthrough)
    if policy.include_platform_essentials:
        allowed |= PLATFORM_ESSENTIALS

    child = {name: value for name, value in parent.items() if name in allowed}

    for name, value in policy.injected:
        if name in child:
            raise EnvironmentDenied(
                "injection_collides_with_passthrough",
                f"{name} is both passed through and injected",
            )
        child[name] = value

    return child


def run(program: str, argv: list[str], parent: dict[str, str],
        policy: EnvironmentPolicy, timeout: int = 10) -> subprocess.CompletedProcess:
    """Launch with the reduced environment and nothing else."""
    return subprocess.run(
        [program, *argv],
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
        env=build_child_environment(parent, policy),
    )
