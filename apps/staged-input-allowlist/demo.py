"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from staging import StagingPolicy, stage  # noqa: E402

POLICY = StagingPolicy(
    allowed_suffixes=frozenset({".py", ".md", ".txt"}),
    denied_names=frozenset({".env", "id_rsa"}),
    max_file_bytes=1024, max_files=10, max_total_bytes=8192,
)


def seed(root):
    files = {"README.md": "# toy\n", "pkg/main.py": "print('toy')\n",
             ".env": "TOKEN=toy-secret-AAAA1111\n",
             "id_rsa": "-----BEGIN PRIVATE KEY-----\n",
             "logo.png": "PNG toy\n", ".git/config": "[core]\n",
             "huge.txt": "x" * 2048}
    for rel, text in files.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        Path(p).write_text(text, encoding="utf-8")


def build() -> Trace:
    tmp = tempfile.mkdtemp(prefix="demo-sia-")
    src, dest = os.path.join(tmp, "repo"), os.path.join(tmp, "staging")
    os.makedirs(src)
    seed(src)
    result = stage(src, dest, POLICY)

    t = Trace(
        app="staged-input-allowlist",
        claim=(
            "Only files matching the declared policy enter the agent's view, every "
            "excluded file is recorded with a fixed-vocabulary reason, and exceeding a "
            "declared cap stages nothing at all."
        ),
        enforcement="deterministic",
        denial_type="StagingRefused",
        redactions={tmp: "<tmp>", tmp.replace("\\", "/"): "<tmp>"},
    )
    t.allow("staging a small repository",
            {"source": "README.md, pkg/main.py, .env, id_rsa, logo.png, .git/config, huge.txt",
             "policy": "suffixes .py .md .txt | denied .env id_rsa | 1 KiB/file"},
            lambda: result.staged,
            evidence=lambda: "only two files entered the agent's view")
    t.allow("every excluded file carries a reason",
            {"excluded": len(result.excluded)},
            lambda: [f"{p} -> {r}" for p, r in result.excluded],
            evidence=lambda: "staged set + excluded set == source set, exactly",
            note="Nothing is dropped without a reason. That is what makes a staging "
                 "policy reviewable: you can ask why any file is missing and get an "
                 "answer.")
    t.allow("the manifest lists exactly the staged set",
            {"manifest": ", ".join(result.manifest)},
            lambda: [p for p, _ in result.excluded if p in result.manifest] or "no excluded path appears in the manifest")

    many = os.path.join(tmp, "many")
    os.makedirs(many)
    seed(many)
    for n in range(12):
        Path(os.path.join(many, f"file_{n}.py")).write_text("toy\n", encoding="utf-8")
    t.deny("a repository over the file-count cap",
           {"admissible files": 14, "max_files": 10},
           lambda: stage(many, os.path.join(tmp, "staging2"), POLICY),
           evidence=lambda: f"staging directory created: "
                            f"{os.path.exists(os.path.join(tmp, 'staging2'))}",
           note="Truncating to the cap would hand the agent a silently partial view — "
                "the worst outcome, because nothing would look wrong.")
    return t


if __name__ == "__main__":
    main(build, __file__)
