"""REH1n: a 3 pm capture the replayed day never had is "not a part of the day" in a rehearsal (N1), decided from the
real record's `main` on or before the day (N2: no look-ahead), never for a capture that existed and recorded nothing
(N3), accepted as quiet by the real code that no real recorder ever hands it (N4), and said once in the exercised line
(N5)."""

import json
import os
import subprocess
from datetime import UTC, date, datetime, timedelta

import pytest

from fno.models import IST
from fno.quotes import cli, indices_cli
from fno.quotes.indices import NOT_A_PART, QUIET_STATUSES, closes_none
from fno.quotes.recorder import DATASET, QuoteSnapshotRecorder, RecordResult
from fno.quotes.weekly import WEEKLY_DATASET
from fno.rehearsal.exercised_line import exercised_line
from fno.rehearsal.part_record import PartRecord
from fno.rehearsal.record_store import RecordReader
from fno.rehearsal.recorded_quotes import RecordedRecorder
from fno.storage.raw_store import LocalFolderStore

D21, D22, D26 = date(2026, 10, 21), date(2026, 10, 22), date(2026, 10, 26)
V4 = "groww/derivatives/quote-snapshots-v4"
SINGLE = {(DATASET, "nifty"): "nifty", (V4, "nifty"): "v4"}  # the single-stem parts (`QuotePart.canonicals`)
PLAN_AT = datetime(2026, 10, 26, 8, 37, 14, tzinfo=UTC)  # the run's first step, 14:07:14 IST


def git(repo, *args, when=None):
    env = {"GIT_COMMITTER_DATE": when.isoformat(), "GIT_AUTHOR_DATE": when.isoformat()} if when else {}
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env={**os.environ, **env})


def put(repo, path, text=""):
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(text)


def commit(repo, when):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "x", when=when)
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")  # the record checkout's view of main


@pytest.fixture
def record(tmp_path):
    """22 Oct is the weekly's first day; BANKNIFTY recorded on 19 Oct and not since; 26 Oct's run planned `v4` and
    `indices` and nothing of `v4` was recorded (a hung part)."""
    repo = tmp_path / "record"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for key, value in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(repo, "config", key, value)
    put(repo, f"research/data/quotes/{WEEKLY_DATASET}/2026/10/niftyweekly_20261022.canonical", "x")
    put(repo, f"research/data/quotes/{DATASET}/2026/10/banknifty_20261019.canonical", "x")
    put(repo, f"research/data/quotes/{DATASET}/2026/10/finnifty_20261021_150250.meta.json", "{}")  # no marker
    put(repo, "journal/runs/2026-10-21.json", json.dumps({"steps": {"quotes": {"inputs": {"parts": ["indices"]}}}}))
    commit(repo, datetime(2026, 10, 22, tzinfo=UTC))
    put(repo, "journal/runs/2026-10-26.json", json.dumps({"steps": {"quotes": {"inputs": {"parts": ["nifty", "v4"]}}}}))
    commit(repo, PLAN_AT)
    return repo


def parts(repo, now=datetime(2026, 10, 27, tzinfo=UTC)):
    return PartRecord(repo, SINGLE, lambda: now)


# N1 and N2: not a part before its first day, a part on it, no look-ahead


def test_the_weekly_is_not_a_part_of_21_oct_and_is_one_of_22_oct(record):
    assert not parts(record).is_part(WEEKLY_DATASET, "niftyweekly", D21)  # 22 Oct's marker is never read for 21
    assert parts(record).is_part(WEEKLY_DATASET, "niftyweekly", D22)  # the boundary: its first day itself


def test_a_multi_stem_part_s_listing_never_makes_a_new_stem_a_part(record):
    """21 Oct's plan named `indices`, while the weekly was not yet one of its stems (judge 639's own example)."""
    assert not parts(record).is_part(WEEKLY_DATASET, "niftyweekly", D21)


# N3: a capture that existed stays one, so a day with nothing is still a failure


def test_a_known_capture_an_attempt_s_sidecar_and_a_planned_single_stem_part_are_parts(record):
    assert parts(record).is_part(DATASET, "banknifty", D21)  # recorded on 19 Oct, nothing on 21
    assert parts(record).is_part(DATASET, "finnifty", D21)  # one attempt's sidecar, no marker (judge 635)
    assert parts(record).is_part(V4, "nifty", D26)  # nothing of v4 at all, but 26 Oct's plan named it (judge 639)


def test_the_plan_counts_only_once_its_commit_is_reached_and_only_from_main(record):
    assert not parts(record, now=PLAN_AT - timedelta(seconds=1)).is_part(V4, "nifty", D26)  # judge 639.1
    assert parts(record, now=PLAN_AT).is_part(V4, "nifty", D26)
    put(record, "journal/runs/2026-10-23.json", json.dumps({"steps": {"quotes": {"inputs": {"parts": ["v4"]}}}}))
    assert not parts(record).is_part(V4, "nifty", date(2026, 10, 23))  # only in the working tree: never counts


def test_an_empty_record_has_no_part(tmp_path):
    assert not PartRecord(tmp_path, SINGLE, lambda: datetime.now(UTC)).is_part(DATASET, "nifty", D21)


# N1 at the recorder: answered before any wait, nothing written


class Never:
    def is_part(self, dataset, stem, day):
        return False


def test_a_capture_that_was_not_a_part_answers_so_at_once_and_writes_nothing(tmp_path):
    now = {"at": datetime(2026, 10, 21, 15, 1, tzinfo=IST)}
    store = LocalFolderStore(tmp_path / "rehearsal")
    live = QuoteSnapshotRecorder(None, store, clock_now=lambda: now["at"], sleep=lambda s: pytest.fail("waited"))
    recorded = RecordedRecorder(live, RecordReader(LocalFolderStore(tmp_path / "record")), Never())
    for result in (recorded.attempt_now(), recorded.record()):
        assert (result.status, result.reason) == (NOT_A_PART, "rehearsal: nifty not recorded on or before 2026-10-21")
    assert list((tmp_path / "rehearsal").rglob("*")) == []  # no file, no sidecar, no "none" marker


# N4: the real code takes it as quiet; no real recorder returns it


def test_not_a_part_is_quiet_never_closed_none_never_alerted_and_exits_0():
    result = RecordResult(NOT_A_PART, reason="rehearsal: niftyweekly not recorded on or before 2026-10-21")
    assert NOT_A_PART in QUIET_STATUSES and not closes_none(result)
    assert not indices_cli._missing(result) and cli.exit_code(result, outside_window=False) == 0


# N5: said once in the exercised line


INDICES_LINES = ["BANKNIFTY recorded: banknifty_20261021_150100 (220 contracts, complete=True)",
                 "NIFTY weekly not a part of the day: - (0 contracts, complete=False) - rehearsal: niftyweekly not "
                 "recorded on or before 2026-10-21"]  # fmt: skip


def test_the_exercised_line_names_each_capture_that_was_not_a_part_once(record):
    v4 = {"status": "ok", "lines": ["not a part of the day: - (0 contracts, complete=False) - rehearsal: nifty ..."]}
    steps = {"quotes_done": {"result": {"status": "ok", "parts": {"indices": {"status": "ok", "lines": INDICES_LINES}},
                                        "exercised_parts": {"v4": v4}}}}  # fmt: skip
    assert exercised_line(steps, day=D21) == (
        "not live in real runs (exercised): quotes_done's indices part: NIFTY weekly not a part of 2026-10-21; "
        "quotes_done's v4 part: not a part of 2026-10-21"
    )


def test_a_day_with_every_capture_a_part_has_no_such_item():
    steps = {
        "quotes_done": {"result": {"status": "ok", "parts": {"indices": {"status": "ok", "lines": INDICES_LINES[:1]}}}}
    }
    assert exercised_line(steps, day=D21) is None
