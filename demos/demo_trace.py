"""Demo trace recorder.

A demo records what the app's REAL module actually did. There is no second
implementation of any app's logic: every step below is produced by calling the
shipped module and writing down what came back, so a demo page cannot show an
outcome the code does not produce.

Each app folder has a `demo.py` that builds a Trace and writes `demo.json`
beside it; `demos/render.py` turns that JSON into a self-contained `demo.html`.
"""

from __future__ import annotations

import json
import platform
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class Step:
    label: str
    request: dict[str, Any]
    outcome: str  # "allowed" or "denied"
    result: str = ""
    reason: str = ""
    detail: str = ""
    evidence: str = ""
    note: str = ""


@dataclass
class Trace:
    app: str
    claim: str
    enforcement: str
    denial_type: str  # the exception class name the app raises
    steps: list[Step] = field(default_factory=list)

    def allow(
        self,
        label: str,
        request: dict[str, Any],
        action: Callable[[], Any],
        evidence: Callable[[], str] | None = None,
        note: str = "",
    ) -> Any:
        """Record a call that is expected to succeed. Fails loudly if it doesn't."""
        value = action()
        self.steps.append(
            Step(
                label=label,
                request=request,
                outcome="allowed",
                result=_render(value),
                evidence=evidence() if evidence else "",
                note=note,
            )
        )
        return value

    def deny(
        self,
        label: str,
        request: dict[str, Any],
        action: Callable[[], Any],
        evidence: Callable[[], str] | None = None,
        note: str = "",
    ) -> Any:
        """Record a call that is expected to be refused.

        If the app does NOT refuse it, this raises — a demo that quietly
        recorded an allow where it promised a deny would be worse than no demo.
        """
        try:
            value = action()
        except Exception as denial:  # the app's own denial exception
            self.steps.append(
                Step(
                    label=label,
                    request=request,
                    outcome="denied",
                    reason=getattr(denial, "reason", type(denial).__name__),
                    detail=str(getattr(denial, "detail", "") or ""),
                    evidence=evidence() if evidence else "",
                    note=note,
                )
            )
            return denial
        raise AssertionError(
            f"{self.app}: step {label!r} was expected to be denied, "
            f"but it returned {value!r}"
        )

    def verdict(
        self,
        label: str,
        request: dict[str, Any],
        action: Callable[[], Any],
        passed: Callable[[Any], bool],
        describe: Callable[[Any], str] | None = None,
        evidence: Callable[[], str] | None = None,
        note: str = "",
    ) -> Any:
        """Record a call that reports pass/fail by return value, not by raising.

        Verification APIs — `ledger.verify()` and friends — hand back a result
        object. The verdict still comes from the real call; only how it is read
        differs.
        """
        value = action()
        ok = bool(passed(value))
        described = describe(value) if describe else _render(value)
        self.steps.append(
            Step(
                label=label,
                request=request,
                outcome="allowed" if ok else "denied",
                result=described if ok else "",
                reason="" if ok else described,
                evidence=evidence() if evidence else "",
                note=note,
            )
        )
        return value

    def write(self, demo_file: str) -> Path:
        out = Path(demo_file).resolve().parent / "demo.json"
        payload = {
            "app": self.app,
            "claim": self.claim,
            "enforcement": self.enforcement,
            "denial_type": self.denial_type,
            "recorded_with": f"CPython {platform.python_version()}",
            "steps": [asdict(step) for step in self.steps],
        }
        out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return out


def _render(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    try:
        return json.dumps(value, default=str)
    except TypeError:
        return repr(value)


def main(build: Callable[[], Trace], demo_file: str) -> None:
    """Entry point for an app's demo.py."""
    trace = build()
    path = trace.write(demo_file)
    print(f"{trace.app}: {len(trace.steps)} steps -> {path.name}", file=sys.stderr)
