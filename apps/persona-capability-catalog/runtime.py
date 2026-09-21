"""Runtime process list: "what's running right now."

A toy in-memory stand-in for a process table. Deliberately has no
knowledge of, and no import of, the persona/capability catalog — see
catalog.py for that, kept fully separate. You can inspect this without
ever loading or validating the catalog, and vice versa.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunningProcess:
    pid: int
    persona_name: str
    started_at: str  # opaque string timestamp; format is irrelevant here


class RuntimeProcessList:
    def __init__(self):
        self._processes: list[RunningProcess] = []

    def register(self, pid: int, persona_name: str, started_at: str) -> None:
        self._processes.append(RunningProcess(pid, persona_name, started_at))

    def list_running(self) -> list[RunningProcess]:
        return list(self._processes)

    def is_running(self, persona_name: str) -> bool:
        return any(p.persona_name == persona_name for p in self._processes)
