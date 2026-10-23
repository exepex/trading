"""What a practice run depended on, for its id (story MS-SIM-e2; orchestrator, 23 Oct): the code commit and the data the
run read that moves from day to day. The archived NSE files are write-once and named by the window, so the window
identifies them; the recorded captures grow every day, so the spread model learned from them is hashed, together with
the margin factor's label. New code or new captures make a new run id, so an archived run is never touched."""

import hashlib
import subprocess
from pathlib import Path

from ..spreads.model import SpreadModel

CODE_PATHS = ("fno", "tools", "config.yaml")  # what a run's behaviour rests on
DIRTY = "the code is not committed ({paths}): a run id names a commit, so commit first or run without --archive"
NO_COMMIT = "cannot name the code commit: {reason}"
COMMIT_CHARS = 12


class CodeNotCommitted(Exception):
    """The checkout differs from the commit the run id would name."""


def code_commit(repository: Path, run=subprocess.run) -> str:
    def git(*args: str) -> list[str]:
        done = run(["git", *args], cwd=repository, capture_output=True, text=True)
        if done.returncode != 0:
            raise CodeNotCommitted(NO_COMMIT.format(reason=(done.stderr or "git failed").strip()))
        return done.stdout.splitlines()  # not stripped: a status line starts with a space

    changed = git("status", "--porcelain", "--untracked-files=all", "--", *CODE_PATHS)
    if changed:
        raise CodeNotCommitted(DIRTY.format(paths=", ".join(line[3:] for line in changed[:3])))
    return git("rev-parse", "HEAD")[0][:COMMIT_CHARS]


def inputs_digest(spreads: SpreadModel, margin_label: str) -> str:
    """The spread model's every (bucket, session, relative half-spread) and the margin factor's label, order-free."""
    rows = sorted(f"{bucket}|{day}|{value!r}" for bucket, days in spreads.by_session.items()
                  for day, value in days.items())  # fmt: skip
    return hashlib.sha256("\n".join([*rows, margin_label]).encode()).hexdigest()
