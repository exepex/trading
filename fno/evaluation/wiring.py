"""Composition root of the evaluation protocol (story S1): the repository, its git history and the research ledger
(B4) the freeze registers in. Swapping any of them changes this file only."""

from __future__ import annotations

from pathlib import Path

from ..config import ROOT
from ..playbook.history import PlaybookGit
from .freeze import ProtocolFreezer


def build_protocol_git(root: Path = ROOT) -> PlaybookGit:
    return PlaybookGit(Path(root))


def build_freezer(root: Path = ROOT) -> ProtocolFreezer:
    return ProtocolFreezer(Path(root), build_protocol_git(root))
