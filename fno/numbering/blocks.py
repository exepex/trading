"""Ledger trial numbers as claimed blocks (story O12e): `numbers/ledger-trial.csv` reserves blocks of trial ids.

A row's number is a block `<a>-<b>` (or one id `<n>`); its name is the experiment prefix the block is for. Every whole
number `trial_id` in `research/ledger.csv` must sit in exactly one block, under an experiment that starts with the
block's name, so two branches never take the same ids and no branch uses another's block. Ids that are not whole
numbers (`book3:<strategy_id>`) are names, not counted ids, and stay outside. Standard library only (the number check).
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path

from fno.numbering.registry import Row, read_rows

LEDGER = "research/ledger.csv"  # B4's LEDGER_FILE, named here so the number check stays standard library only
BLOCK = re.compile(r"([1-9]\d*)(?:-([1-9]\d*))?")
CLAIM_COMMAND = "python tools/claim_number.py ledger-trial <experiment-prefix> --session <id> --count <k>"

UNCOVERED = "{ledger}: trial {id} ({experiment}) is in no block of {registry}; claim one first: {command}"
OUTSIDE = "{ledger}: trial {id}'s experiment {experiment} does not start with its block's name {name} (block {block})"
OVERLAP = "{registry}: blocks {first} ({first_name}) and {second} ({second_name}) overlap"
NOT_CLAIMED = "trial {id} is in no block of {registry}: claim one first ({command}), then merge main into your branch"
OTHER_BLOCK = "trial {id} sits in block {block}, claimed for experiment {name!r}, not {experiment!r}"
NO_FREE = "no free id in a block claimed for experiment {experiment!r} in {registry}: claim one ({command})"


@dataclass(frozen=True)
class Block:
    first: int
    last: int
    name: str

    @property
    def text(self) -> str:
        return str(self.first) if self.first == self.last else f"{self.first}-{self.last}"

    def covers(self, trial_id: int) -> bool:
        return self.first <= trial_id <= self.last

    def overlaps(self, other: Block) -> bool:
        return self.first <= other.last and other.first <= self.last

    def is_for(self, experiment: str) -> bool:
        """The experiment is the block's name, or starts with it then '-' (`edge2-f6` takes `edge2-f6-x`, never
        `edge2-f60`)."""
        return experiment == self.name or experiment.startswith(self.name + "-")


@dataclass(frozen=True)
class Trial:
    id: int
    experiment: str


def parse_block(number: str, name: str = "") -> Block | None:
    found = BLOCK.fullmatch(number)
    if not found:
        return None
    first = int(found.group(1))
    last = int(found.group(2) or first)
    return Block(first, last, name) if first <= last else None


def ledger_trials(root: Path) -> list[Trial]:
    """The ledger's whole-number trials, in file order; no ledger is no trials."""
    path = root / LEDGER
    if not path.is_file():
        return []
    rows = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")))
    return [Trial(int(r["trial_id"]), r["experiment"]) for r in rows if r["trial_id"].isdigit()]


class BlockSeries:
    """The `ledger-trial` series: what the claim tool, the check and the seed need of it."""

    name = "ledger-trial"
    registry = "numbers/ledger-trial.csv"

    def valid_number(self, number: str) -> bool:
        return parse_block(number) is not None

    def claimed_name(self, number: str, slug: str) -> str:
        return slug

    def next_step(self, number: str, name: str) -> str:
        return (
            f"merge main into your branch (git pull --no-rebase origin main), then register trials {number} "
            f"with an experiment that starts with {name!r}"
        )

    def blocks(self, root: Path) -> list[Block]:
        return well_formed(read_rows(root / self.registry))

    def next_block(self, root: Path, count: int) -> str:
        """The `count` ids after every block end and every ledger id on this tree."""
        start = 1 + max([b.last for b in self.blocks(root)] + [t.id for t in ledger_trials(root)], default=0)
        return Block(start, start + count - 1, "").text

    def overlapping(self, root: Path, block: Block) -> list[Block]:
        taken = self.blocks(root) + [Block(t.id, t.id, t.experiment) for t in ledger_trials(root)]
        return [b for b in taken if b.overlaps(block)]


LEDGER_TRIAL = BlockSeries()


def well_formed(rows: list[Row]) -> list[Block]:
    return [b for b in (parse_block(r.number, r.name) for r in rows) if b is not None]


def block_findings(rows: list[Row], trials: list[Trial]) -> list[str]:
    """Overlapping blocks, trials in no block and trials under another experiment's block; the rows' own form is
    checked like every series (`check._bad_rows`)."""
    blocks = sorted(well_formed(rows), key=lambda b: (b.first, b.last))
    found = [
        OVERLAP.format(
            registry=LEDGER_TRIAL.registry, first=a.text, first_name=a.name, second=b.text, second_name=b.name
        )  # fmt: skip
        for i, a in enumerate(blocks)
        for b in blocks[i + 1 :]
        if a.overlaps(b)
    ]
    for trial in trials:
        owner = next((b for b in blocks if b.covers(trial.id)), None)
        if owner is None:
            found.append(UNCOVERED.format(ledger=LEDGER, id=trial.id, experiment=trial.experiment,
                                          registry=LEDGER_TRIAL.registry, command=CLAIM_COMMAND))  # fmt: skip
        elif not owner.is_for(trial.experiment):
            found.append(OUTSIDE.format(ledger=LEDGER, id=trial.id, experiment=trial.experiment, name=owner.name,
                                        block=owner.text))  # fmt: skip
    return found


def seed_blocks(trials: list[Trial], rows: list[Row]) -> list[Block]:
    """History rows for the trials no block covers yet: one block per run of consecutive ids with one experiment."""
    covered = well_formed(rows)
    runs: list[Block] = []
    for trial in sorted((t for t in trials if not any(b.covers(t.id) for b in covered)), key=lambda t: t.id):
        last = runs[-1] if runs else None
        if last is not None and last.name == trial.experiment and last.last == trial.id - 1:
            runs[-1] = Block(last.first, trial.id, last.name)
        else:
            runs.append(Block(trial.id, trial.id, trial.experiment))
    return runs


class TrialClaims:
    """The claims `Ledger.register` and the evaluation freeze read: the blocks in this checkout's registry."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def problem(self, trial_id: str, experiment: str) -> str | None:
        """Why this trial may not be registered here, or None; an id that is not a whole number is not counted."""
        if not trial_id.isdigit():
            return None
        owner = next((b for b in LEDGER_TRIAL.blocks(self.root) if b.covers(int(trial_id))), None)
        if owner is None:
            return NOT_CLAIMED.format(id=trial_id, registry=LEDGER_TRIAL.registry, command=CLAIM_COMMAND)
        if not owner.is_for(experiment):
            return OTHER_BLOCK.format(id=trial_id, block=owner.text, name=owner.name, experiment=experiment)
        return None

    def next_free(self, experiment: str, used: set[str]) -> str:
        """The lowest unused id of a block claimed for this experiment; never one from another block."""
        for block in sorted(LEDGER_TRIAL.blocks(self.root), key=lambda b: b.first):
            if block.is_for(experiment):
                free = next((n for n in range(block.first, block.last + 1) if str(n) not in used), None)
                if free is not None:
                    return str(free)
        raise ValueError(NO_FREE.format(experiment=experiment, registry=LEDGER_TRIAL.registry, command=CLAIM_COMMAND))
