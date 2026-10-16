"""The research ledger guard (story B4): no trial runs unless it was registered first, proved by git history.

`research/ledger.csv` is the machine record (one row per trial); `research/LEDGER.md` is the readable history. A trial
may run only if:
1. the ledger file equals the committed HEAD version (no staged or unstaged edits), and the commit that first added
   the trial's row is an ancestor of the commit being run (registration is in history and cannot be back-dated);
2. it names a frozen protocol (commit and file) that is an ancestor of the commit being run;
3. the protocol file is unchanged since that frozen commit.
Trials 1-31 were recorded while or after being run: they are `retrospective` and never presented as pre-registered.
"""

from __future__ import annotations

import csv
import io
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

LEDGER_FILE = "research/ledger.csv"
COLUMNS = (
    "trial_id", "experiment", "description", "kind", "hypothesis", "registered_on", "protocol_path",
    "protocol_commit", "first_run_on", "run_commit",
)  # fmt: skip
KINDS = ("retrospective", "prospective", "control")


class NotRegistered(RuntimeError):
    """The trial may not run: it is missing, not committed, or its protocol is not frozen and unchanged."""


@dataclass(frozen=True)
class Git:
    """The few git questions the guard asks, against one repository folder."""

    root: Path

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)

    def head(self) -> str:
        return self._run("rev-parse", "HEAD").stdout.strip()

    def is_ancestor(self, older: str, newer: str) -> bool:
        return bool(older) and self._run("merge-base", "--is-ancestor", older, newer).returncode == 0

    def first_commit_containing(self, text: str, path: str) -> str | None:
        """The earliest commit whose change to `path` added `text` (git's pickaxe search)."""
        found = self._run("log", "--format=%H", "--reverse", "-S", text, "--", path).stdout.split()
        return found[0] if found else None

    def committed_text(self, path: str, commit: str = "HEAD") -> str | None:
        """The file as committed at `commit` (None if not committed there)."""
        result = self._run("show", f"{commit}:{path}")
        return result.stdout if result.returncode == 0 else None

    def commits_touching(self, path: str) -> list[str]:
        """Every commit that changed `path`, oldest first (story D5: the strategy registry's append-only check)."""
        return self._run("log", "--format=%H", "--reverse", "--", path).stdout.split()

    def changes_with_parents(self, path: str, revision: str = "HEAD") -> list[tuple[str, tuple[str, ...]]]:
        """Every commit in `revision`'s history that changed `path` against any of its parents, merges included, each
        with its real parents (story D5: a merge of parallel registrations is two appends, not an edit)."""
        lines = self._run("log", "--format=%H %P", "--full-history", revision, "--", path).stdout.splitlines()
        return [(line.split()[0], tuple(line.split()[1:])) for line in lines if line.strip()]

    def is_shallow(self) -> bool:
        """A shallow clone lacks the older history, so a history check would pass on what it cannot see."""
        return self._run("rev-parse", "--is-shallow-repository").stdout.strip() != "false"

    def commit_exists(self, commit: str) -> bool:
        return bool(commit) and self._run("cat-file", "-e", f"{commit}^{{commit}}").returncode == 0

    def unchanged_since(self, commit: str, path: str) -> bool:
        tracked = self._run("diff", "--quiet", commit, "HEAD", "--", path).returncode == 0
        untouched = self._run("diff", "--quiet", "HEAD", "--", path).returncode == 0
        return tracked and untouched


def read_ledger(text: str) -> list[dict]:
    rows = list(csv.DictReader(io.StringIO(text)))
    for row in rows:
        if tuple(row) != COLUMNS:
            raise ValueError(f"ledger columns must be {COLUMNS}")
        if row["kind"] not in KINDS or row["hypothesis"] not in ("yes", "no"):
            raise ValueError(f"trial {row['trial_id']}: bad kind or hypothesis flag")
    ids = [r["trial_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate trial ids in the ledger")
    return rows


def write_ledger(rows: list[dict]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


class Ledger:
    def __init__(self, root: Path, git: Git | None = None):
        self.root, self.git = Path(root), git or Git(Path(root))
        self.file = self.root / LEDGER_FILE

    def rows(self) -> list[dict]:
        return read_ledger(self.file.read_text()) if self.file.is_file() else []

    def register(self, trial_id: str, experiment: str, description: str, kind: str, hypothesis: bool,
                 protocol_path: str = "", today: date | None = None) -> None:  # fmt: skip
        """Adds a row (commit it before the trial runs)."""
        rows = self.rows()
        if any(r["trial_id"] == trial_id for r in rows):
            raise ValueError(f"trial {trial_id} is already registered")
        row = dict.fromkeys(COLUMNS, "")
        row.update(trial_id=trial_id, experiment=experiment, description=description, kind=kind,
                   hypothesis="yes" if hypothesis else "no", registered_on=(today or date.today()).isoformat(),
                   protocol_path=protocol_path)  # fmt: skip
        read_ledger(write_ledger([*rows, row]))  # validates
        self.file.write_text(write_ledger([*rows, row]))

    def require_committed(self, trial_id: str) -> dict:
        """The trial's row if its registration is committed history (no protocol check): enough to run an already
        looked-at period, never the one that decides. NotRegistered with the reason otherwise."""
        row = next((r for r in self.rows() if r["trial_id"] == trial_id), None)
        if row is None:
            raise NotRegistered(f"trial {trial_id} is not registered: it is not in {LEDGER_FILE}")
        committed = self.git.committed_text(LEDGER_FILE)
        if committed is None or not self.git.unchanged_since("HEAD", LEDGER_FILE):
            raise NotRegistered("the ledger has uncommitted changes: commit it so the run uses exactly what is in git")
        if row not in read_ledger(committed):
            raise NotRegistered(f"trial {trial_id}: its row differs from the committed ledger")
        registered = self.git.first_commit_containing(f"\n{trial_id},", LEDGER_FILE)
        if not registered or not self.git.is_ancestor(registered, self.git.head()):
            raise NotRegistered(f"trial {trial_id} is not in a committed ledger (commit the registration first)")
        return row

    def require_registered(self, trial_id: str) -> dict:
        """The trial's row if it may run now; NotRegistered with the reason otherwise. Call before reading any data."""
        row = self.require_committed(trial_id)
        if not row["protocol_commit"] or not row["protocol_path"]:
            raise NotRegistered(f"trial {trial_id} has no frozen protocol commit")
        if not self.git.is_ancestor(row["protocol_commit"], self.git.head()):
            raise NotRegistered(f"trial {trial_id}: protocol commit {row['protocol_commit'][:10]} is not in history")
        if not self.git.unchanged_since(row["protocol_commit"], row["protocol_path"]):
            raise NotRegistered(f"trial {trial_id}: {row['protocol_path']} changed after it was frozen")
        return row

    def mark_run(self, trial_id: str, today: date | None = None) -> None:
        """Records the first run once (date and commit); later runs never change it."""
        rows = self.rows()
        for row in rows:
            if row["trial_id"] == trial_id and not row["first_run_on"]:
                row["first_run_on"], row["run_commit"] = (today or date.today()).isoformat(), self.git.head()
        self.file.write_text(write_ledger(rows))

    def count(self, experiment: str) -> dict[str, int]:
        rows = [r for r in self.rows() if r["experiment"] == experiment]
        return {"registered_rows": len(rows), "hypotheses": sum(r["hypothesis"] == "yes" for r in rows)}
