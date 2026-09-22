"""Argv, not shell, invocation.

A child process is launched from an absolute program path and a list of
argument values. There is no shell, so there is no metacharacter with meaning:
a semicolon in an argument is a semicolon, not a second command.

The check is not "does this argument look dangerous". It is "is this argument
ever interpreted", and the answer is no, by construction. Sanitizing a shell
string is a guess about a grammar; not building one is a fact about it.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


class InvocationDenied(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Invocation:
    program: str
    argv: tuple[str, ...]


def build_invocation(program: str, arguments: list[str]) -> Invocation:
    """Validate the shape of a launch, or refuse.

    Rejects the two shapes that reintroduce a shell:

    - a relative program name, which resolves through PATH and so names a
      different file depending on where and how the process was started;
    - a single string standing in for the whole command line, which can only
      be turned into a process by something that parses it.
    """
    if not program or not program.strip():
        raise InvocationDenied("empty_program", "no program given")

    if isinstance(arguments, str):
        raise InvocationDenied(
            "shell_string_argument",
            "arguments must be a list of values, not one command line",
        )

    if not os.path.isabs(program):
        raise InvocationDenied("relative_program", program)

    for index, argument in enumerate(arguments):
        if not isinstance(argument, str):
            raise InvocationDenied("non_string_argument", f"argv[{index}]={argument!r}")

    return Invocation(program=program, argv=tuple(arguments))


def run(invocation: Invocation, timeout: int = 10) -> subprocess.CompletedProcess:
    """Launch without a shell. `shell=True` is never used anywhere in this app."""
    return subprocess.run(
        [invocation.program, *invocation.argv],
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )
