"""Story O8 criterion 2 for the 3 pm recorders, forecast v2's records and the AI books: each status from its evidence,
by the row's own deciding time (push receipt for the canonical and the commitment, in-file `generated_at` for the
forecast rows), with the boundary exactly at the deadline."""

import csv
import io

import pytest

from fno.ai.paths import commitment_path, fired_path, records_path, reveal_path, rules_path
from fno.ai.timing import LATEST_START
from fno.constants import (
    BOOK2_HYBRID,
    HEALTH_LATE,
    HEALTH_MISSED,
    HEALTH_NOT_DUE,
    HEALTH_OK,
)
from fno.forecast.schema_v2 import GENERATION_DEADLINE
from fno.health.forecast_checks import AiBookCheck, ForecastRowsCheck
from fno.health.model import Deadline, EvidenceUnknown
from fno.health.quote_checks import QUOTES_FOLDER, CanonicalCheck
from fno.quotes.recorder import DATASET

from .fakes import DAY, Repo, ist

CANONICAL = f"{QUOTES_FOLDER}/{DATASET}/2026/10/nifty_20261015.canonical"
SIDECAR = f"{QUOTES_FOLDER}/{DATASET}/2026/10/nifty_20261015_145600.meta.json"
EVENING = ist(DAY, 17, 51)
AT_1500, AT_1510, AT_1512 = ist(DAY, 15, 0), ist(DAY, 15, 10), ist(DAY, 15, 12)


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)


def _recorded(repo, complete=True, in_window=True, pushed=AT_1500):
    repo.write(CANONICAL, "nifty_20261015_145600\n")
    repo.write_json(SIDECAR, {"complete": complete, "in_window": in_window})
    repo.receipts.file(CANONICAL, pushed)


def _canonical(repo):
    return CanonicalCheck(repo.evidence, DATASET, Deadline(LATEST_START))


@pytest.mark.parametrize(("pushed", "status"), [(ist(DAY, 15, 13), HEALTH_OK), (ist(DAY, 15, 13, 1), HEALTH_LATE)])
def test_a_canonical_is_on_time_by_its_push_up_to_1513_exactly(repo, pushed, status):
    _recorded(repo, pushed=pushed)
    result = _canonical(repo).check(DAY, EVENING)
    assert result.status == status and (status == HEALTH_OK or "due 15 Oct 15:13" in result.detail)


@pytest.mark.parametrize(
    ("plant", "detail"),
    [
        (lambda r: r.write(CANONICAL, "none\n"), "none"),
        (lambda r: _recorded(r, complete=False), "incomplete"),
        (lambda r: _recorded(r, in_window=False), "incomplete"),
        (lambda r: None, "never ran"),
    ],
)
def test_none_incomplete_and_absent_canonicals_are_misses(repo, plant, detail):
    plant(repo)
    result = _canonical(repo).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and detail in result.detail


def test_an_absent_canonical_is_not_due_before_1513(repo):
    assert _canonical(repo).check(DAY, ist(DAY, 15, 12)).status == HEALTH_NOT_DUE


def test_a_canonical_whose_sidecar_is_not_committed_is_unknown(repo):
    repo.write(CANONICAL, "nifty_20261015_145600\n")
    with pytest.raises(EvidenceUnknown, match="sidecar"):
        _canonical(repo).check(DAY, EVENING)


def test_a_canonical_whose_push_github_does_not_show_is_unknown(repo):
    _recorded(repo)
    repo.receipts.pushes.clear()
    with pytest.raises(EvidenceUnknown, match="push time unknown"):
        _canonical(repo).check(DAY, EVENING)


def _rows(repo, count=20, last=AT_1510, blank=0):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=("book", "question", "probability", "generated_at"))
    writer.writeheader()
    for i in range(count):
        when = last if i == count - 1 else ist(DAY, 15, 0)
        writer.writerow({"book": "b", "question": f"q{i}", "probability": "" if i < blank else "0.5",
                         "generated_at": when.isoformat()})  # fmt: skip
    repo.write(rules_path(DAY), out.getvalue())


def _forecasts(repo, expected=20):
    return ForecastRowsCheck(repo.evidence, expected, Deadline(GENERATION_DEADLINE))


@pytest.mark.parametrize(("last", "status"), [(ist(DAY, 15, 15), HEALTH_OK), (ist(DAY, 15, 15, 1), HEALTH_LATE)])
def test_forecast_rows_are_on_time_by_their_own_generated_at(repo, last, status):
    _rows(repo, last=last, blank=10)
    result = _forecasts(repo).check(DAY, EVENING)
    assert result.status == status and "10 of 20 blank" in result.detail  # blanks are shown, never a failure


@pytest.mark.parametrize("count", [19, 21, 0])
def test_any_other_row_count_than_expected_is_a_miss(repo, count):
    _rows(repo, count=count)
    result = _forecasts(repo).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and f"({count} written)" in result.detail


def test_twenty_rows_that_repeat_a_forecaster_and_question_are_a_miss(repo):
    _rows(repo)
    path = repo.root / rules_path(DAY)
    lines = path.read_text().splitlines()
    path.write_text("\n".join([lines[0], *[lines[1]] * 20]) + "\n")
    result = _forecasts(repo).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and "1 distinct of 20 rows" in result.detail


def test_absent_forecast_records_are_not_due_until_the_collection_end_then_missed(repo):
    assert _forecasts(repo).check(DAY, ist(DAY, 15, 29)).status == HEALTH_NOT_DUE
    assert _forecasts(repo).check(DAY, ist(DAY, 15, 30, 1)).status == HEALTH_MISSED


def test_an_unreadable_generated_at_is_unknown(repo):
    repo.write(rules_path(DAY), "book,question,generated_at\n" + "".join(f"b,q{i},soon\n" for i in range(20)))
    with pytest.raises(EvidenceUnknown):
        _forecasts(repo).check(DAY, EVENING)


def _sealed(repo, pushed=AT_1512, revealed=True, entry=None):
    repo.write_json(fired_path(DAY), {BOOK2_HYBRID: entry or {"fired": True}})
    repo.write(commitment_path(DAY, BOOK2_HYBRID), "{}")
    repo.receipts.file(commitment_path(DAY, BOOK2_HYBRID), pushed)
    if revealed:
        repo.write(reveal_path(DAY, BOOK2_HYBRID), "{}")
        repo.write(records_path(DAY, BOOK2_HYBRID), "book\n")


@pytest.mark.parametrize(("pushed", "status"), [(ist(DAY, 15, 15), HEALTH_OK), (ist(DAY, 15, 15, 1), HEALTH_LATE)])
def test_an_ai_commitment_is_on_time_by_its_push_up_to_1515(repo, pushed, status):
    _sealed(repo, pushed=pushed)
    assert AiBookCheck(repo.evidence, BOOK2_HYBRID).check(DAY, EVENING).status == status


def test_a_book_not_fired_shows_the_fire_logs_reason(repo):
    _sealed(repo, entry={"fired": False, "reason": "stop rule: paused by the owner"})
    result = AiBookCheck(repo.evidence, BOOK2_HYBRID).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and "stop rule: paused by the owner" in result.detail


def test_a_missing_reveal_is_not_due_before_1530_and_missed_after(repo):
    _sealed(repo, revealed=False)
    assert AiBookCheck(repo.evidence, BOOK2_HYBRID).check(DAY, ist(DAY, 15, 20)).status == HEALTH_NOT_DUE
    result = AiBookCheck(repo.evidence, BOOK2_HYBRID).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and "reveal" in result.detail


def test_no_fire_log_means_the_ai_run_never_started(repo):
    result = AiBookCheck(repo.evidence, BOOK2_HYBRID).check(DAY, EVENING)
    assert result.status == HEALTH_MISSED and "never ran" in result.detail
