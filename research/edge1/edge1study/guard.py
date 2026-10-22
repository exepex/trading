"""Protocol section 13: both runs refuse unless every study file matches its `FREEZE.md` hash and the study folder is
clean; run 2 also refuses unless `selection.json` is committed and unchanged, and unless no `final.json` exists now or
in any earlier commit. GR1's guard, with EDGE1's folder (git is injected, so the tests use a temporary repository)."""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

CODE_SECTION = "## Analysis code"
ROW = re.compile(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$")
STUDY = "research/edge1"


class Refused(RuntimeError):
    """A run that must not start."""


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def frozen_hashes(freeze_text: str) -> dict[str, str]:
    if CODE_SECTION not in freeze_text:
        raise Refused("FREEZE.md has no frozen analysis code yet")
    section = freeze_text.split(CODE_SECTION, 1)[1]
    return {m.group(1): m.group(2) for line in section.splitlines() if (m := ROW.match(line.strip()))}


def check_code(root: Path) -> None:
    study = root / STUDY
    hashes = frozen_hashes((study / "FREEZE.md").read_text(encoding="utf-8"))
    present = {p.relative_to(study).as_posix() for p in study.rglob("*.py") if "__pycache__" not in p.parts}
    if missing := present - set(hashes):
        raise Refused(f"study files without a frozen hash: {sorted(missing)}")
    for name, digest in hashes.items():
        path = study / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise Refused(f"{name}: differs from its FREEZE.md hash")
    if git(root, "status", "--porcelain", "--", STUDY).strip():
        raise Refused(f"{STUDY} has uncommitted changes")


def check_final_allowed(root: Path) -> None:
    selection, final = f"{STUDY}/selection.json", f"{STUDY}/final.json"
    if not git(root, "log", "--format=%H", "--", selection).strip():
        raise Refused("selection.json is not committed: run 1 first, then commit it")
    if git(root, "status", "--porcelain", "--", selection).strip():
        raise Refused("selection.json differs from its commit")
    if (root / final).exists() or git(root, "log", "--all", "--format=%H", "--", final).strip():
        raise Refused("final.json exists now or in an earlier commit: run 2 is read once")
