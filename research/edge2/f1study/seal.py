"""The held-out seal (protocol sections 2 and 9): FINNIFTY and MIDCPNIFTY rows are loaded only after the discovery
results file is committed and unchanged, and only when it nominated a variant."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

DISCOVERY_SYMBOLS = ("NIFTY", "BANKNIFTY")
HELD_OUT_SYMBOLS = ("FINNIFTY", "MIDCPNIFTY")


class SealBroken(RuntimeError):
    """The held-out read was asked for before its conditions held."""


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def committed_unchanged(root: Path, path: Path) -> bool:
    relative = str(path.relative_to(root))
    tracked = _git(root, "ls-files", "--error-unmatch", relative).returncode == 0
    clean = _git(root, "diff", "--quiet", "HEAD", "--", relative).returncode == 0
    return tracked and clean


def nominated_for_held_out(root: Path, discovery: Path) -> list[str]:
    """The discovery run's nominees, once its file is committed and unchanged; SealBroken otherwise or if none."""
    if not discovery.is_file() or not committed_unchanged(root, discovery):
        raise SealBroken(f"{discovery.name} is not committed and unchanged: the held-out set stays closed")
    nominees = json.loads(discovery.read_text(encoding="utf-8"))["nominated"]
    if not nominees:
        raise SealBroken("discovery nominated nothing: the held-out set is not read (protocol section 9)")
    return nominees


def allowed(symbols, held_out_open: bool) -> None:
    """Refuse any held-out symbol unless the seal was opened by `nominated_for_held_out`."""
    if not held_out_open and any(s in HELD_OUT_SYMBOLS for s in symbols):
        raise SealBroken("held-out symbols requested before the seal opened")
