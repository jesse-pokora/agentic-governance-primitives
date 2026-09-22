"""Render every app's demo.json into a self-contained demo.html.

The page is a view over the recorded trace. It contains no app logic — it
cannot show an outcome the recorded run did not produce.

    python demos/render.py            # render every app that has a demo.json
    python demos/render.py <app-dir>  # render one
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "template.html"


def render_one(app_dir: Path) -> Path | None:
    trace_file = app_dir / "demo.json"
    if not trace_file.exists():
        return None

    trace = json.loads(trace_file.read_text(encoding="utf-8"))
    template = TEMPLATE.read_text(encoding="utf-8")

    # Embedded in a <script type="application/json">, so the only sequence that
    # can break out is a literal "</script>".
    payload = json.dumps(trace, indent=2).replace("</", "<\/")

    html = template.replace("__APP__", trace["app"]).replace("__TRACE__", payload)
    out = app_dir / "demo.html"
    out.write_text(html, encoding="utf-8")
    return out


def main(argv: list[str]) -> int:
    targets = (
        [Path(argv[0]).resolve()]
        if argv
        else sorted(p for p in (ROOT / "apps").iterdir() if p.is_dir())
    )
    rendered = [out for target in targets if (out := render_one(target))]
    for out in rendered:
        print(f"rendered {out.relative_to(ROOT).as_posix()}")
    print(f"{len(rendered)} demo page(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
