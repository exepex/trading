"""F1t's check of a decided run before it is committed (story F1t criterion 7): one run of the book's day, under its
folder and its write paths, unedited since written, every record a valid D3 record carrying the pointer's book,
pack hashes, the model reported, the fire log's session and the decision version in `served`. Any problem means the
run is never committed and the book-day is `refused`."""

from __future__ import annotations

import json
from pathlib import Path

from ..playbook.decision_record import RecordError, validate_record
from ..playbook.decision_store import INPUTS_FILE, SUMS_FILE, DecisionStore
from .ports import AcceptedDecision, DecidedRun
from .write_snapshot import is_under


def run_problems(
    root: Path, decided: DecidedRun, accepted: AcceptedDecision, write_paths: tuple[str, ...]
) -> list[str]:
    store = DecisionStore(root, accepted.book)
    runs = [run for run in store.every_run() if run.parent == store.day_folder(accepted.day)]  # how many, not which
    if not decided.run.is_dir() or decided.run.resolve() not in [r.resolve() for r in runs]:
        return [f"{decided.run} is not a run of {accepted.book} on {accepted.day}"]
    problems = [] if len(runs) == 1 else [f"{len(runs)} runs of {accepted.book} on {accepted.day}: only one may exist"]
    outside = [str(p) for p in (decided.run, *decided.files) if not is_under(root, p, write_paths)]
    problems += [f"written outside the version's write paths: {', '.join(outside)}"] if outside else []
    edited = DecisionStore.edited(decided.run)
    problems += [f"files changed after the run was written: {', '.join(edited)}"] if edited else []
    for record in sorted(p for p in decided.run.glob("*.json") if p.name not in (INPUTS_FILE, SUMS_FILE)):
        problems += [f"{record.name}: {p}" for p in record_problems(json.loads(record.read_text("utf-8")), accepted)]
    return problems


def record_problems(record: dict, accepted: AcceptedDecision) -> list[str]:
    try:
        validate_record(record)
    except RecordError as wrong:
        return [str(wrong)]
    expected = {"book": accepted.book, "common_pack_sha256": accepted.common_pack.sha256,
                "private_pack_sha256": accepted.private_pack.sha256, "model_served": accepted.model_reported,
                "session_id": accepted.session}  # fmt: skip
    problems = [
        f"{key} is {record.get(key)!r}, not {value!r}" for key, value in expected.items() if record.get(key) != value
    ]
    if accepted.version not in record["served"].values():
        problems.append("served does not name the decision version")
    return problems
