"""Recorded demonstration. Run: python demo.py && python ../../demos/render.py ."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "demos"))

from demo_trace import Trace, main  # noqa: E402
from launcher import (  # noqa: E402
    HashPinnedLauncher, PinnedIdentity, PinnedIdentityPolicy, sha256_of_file,
)

TOOL = b"#!/bin/sh\necho toy-deploy-tool v1\n"


def build() -> Trace:
    tmp = tempfile.mkdtemp(prefix="demo-hpi-")
    trusted_dir, attacker_dir = os.path.join(tmp, "trusted_bin"), os.path.join(tmp, "attacker_bin")
    os.makedirs(trusted_dir); os.makedirs(attacker_dir)
    trusted = os.path.join(trusted_dir, "deploy-tool")
    Path(trusted).write_bytes(TOOL)
    pinned_hash = sha256_of_file(trusted)
    launcher = HashPinnedLauncher(
        PinnedIdentityPolicy({"deploy-tool": PinnedIdentity(trusted, pinned_hash)})
    )

    t = Trace(
        app="hash-pinned-identity",
        claim=(
            "A launcher refuses to run any executable whose resolved absolute path and "
            "SHA-256 don't both match a policy pinned outside the workspace — even if the "
            "name on PATH is identical."
        ),
        enforcement="deterministic",
        denial_type="IdentityMismatch",
        # Details are built with repr(), which doubles backslashes on Windows,
        # so the escaped spelling is redacted first — before the plain one
        # could match half of it.
        redactions={
            tmp.replace("\\", "\\\\"): "<tmp>",
            tmp.replace("\\", "/"): "<tmp>",
            tmp: "<tmp>",
        },
    )
    t.allow("the pinned path, with the pinned contents",
            {"name": "deploy-tool", "path": "trusted_bin/deploy-tool",
             "sha256": pinned_hash[:16] + "..."},
            lambda: launcher.launch("deploy-tool", trusted),
            evidence=lambda: "both path and hash matched the pinned identity")

    impostor = os.path.join(attacker_dir, "deploy-tool")
    Path(impostor).write_bytes(TOOL)  # byte-identical
    t.deny("an impostor earlier on PATH, byte-identical contents",
           {"name": "deploy-tool", "path": "attacker_bin/deploy-tool",
            "sha256": sha256_of_file(impostor)[:16] + "..."},
           lambda: launcher.launch("deploy-tool", impostor),
           note="Identical bytes are not enough. The pin is path AND hash, so a "
                "same-named file in another directory is a different identity.")

    Path(trusted).write_bytes(b"#!/bin/sh\necho backdoored\n")
    t.deny("the pinned path, contents tampered with",
           {"name": "deploy-tool", "path": "trusted_bin/deploy-tool",
            "sha256": sha256_of_file(trusted)[:16] + "..."},
           lambda: launcher.launch("deploy-tool", trusted),
           note="The correct location is not enough either.")

    t.deny("a name the policy never pinned",
           {"name": "unregistered-tool", "path": "trusted_bin/deploy-tool"},
           lambda: launcher.launch("unregistered-tool", trusted),
           note="Unknown means refused, never 'probably fine'.")
    return t


if __name__ == "__main__":
    main(build, __file__)
