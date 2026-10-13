"""Replay of a live forecast day (G1 protocol v3; ChatGPT review 30 item 5, response 69).

The panel on `main` grows every evening (story A13), so the panel a live forecast read is not today's: it is the panel
at the parent of the commit that added that day's records (the capture committed its records on top of the checkout it
computed from). A replay exports the inputs from that parent commit (the panel and its official closes, the quote
snapshots, the session calendar and `config.yaml`), recomputes the day with the recorded generation time, and compares
the pack and the records byte for byte with the committed ones. Read-only: it never writes to the repository.
"""

from __future__ import annotations

import io
import subprocess
import tarfile
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..forecast.capture import LIVE_FOLDER
from ..forecast.record_files import read_records_v2

REPLAY_INPUTS = ("research/data/nifty-panel", "research/data/quotes", "research/data/calendar", "config.yaml")
OUTPUTS = ("pack.json", "forecasts.csv")
Recompute = Callable[[Path, date, datetime], dict[str, bytes]]  # (exported inputs, day, generated_at) -> outputs


@dataclass(frozen=True)
class ReplayResult:
    day: date
    records_commit: str
    inputs_commit: str  # the records commit's first parent: what the capture read
    same: dict[str, bool]  # output name -> equal to the committed bytes

    @property
    def matches(self) -> bool:
        return all(self.same.values())


class LiveReplay:
    def __init__(self, root: Path, recompute: Recompute):
        self.root, self.recompute = Path(root), recompute

    def replay(self, day: date) -> ReplayResult:
        paths = {name: f"{LIVE_FOLDER}/{day:%Y}/{day.isoformat()}_{name}" for name in OUTPUTS}
        commit = self._first_commit_adding(paths["forecasts.csv"])
        parent = self._git("rev-parse", f"{commit}^1").decode().strip()
        committed = {name: self._git("show", f"{commit}:{path}") for name, path in paths.items()}
        generated = read_records_v2(committed["forecasts.csv"].decode("utf-8"))[0].generated_at
        with tempfile.TemporaryDirectory() as folder:
            self._export(parent, Path(folder))
            outputs = self.recompute(Path(folder), day, generated)
        return ReplayResult(day, commit, parent, {name: outputs[name] == committed[name] for name in OUTPUTS})

    def _first_commit_adding(self, path: str) -> str:
        found = self._git("log", "--diff-filter=A", "--format=%H", "--", path).decode().split()
        if not found:
            raise FileNotFoundError(f"no commit added {path}")
        return found[-1]

    def _export(self, commit: str, folder: Path) -> None:
        for path in REPLAY_INPUTS:
            if subprocess.run(["git", "cat-file", "-e", f"{commit}:{path}"], cwd=self.root).returncode != 0:
                continue  # an input that did not exist then (e.g. no quote snapshot folder yet)
            with tarfile.open(fileobj=io.BytesIO(self._git("archive", commit, path))) as archive:
                archive.extractall(folder, filter="data")

    def _git(self, *args: str) -> bytes:
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, check=True).stdout
