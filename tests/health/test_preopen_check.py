"""A22's witness in O8 (criterion 8): the pre-open day row's receipt judged by its push time against 09:15, when
FL1's report reads it (O8's owner, review of a2b2ad8c)."""

from __future__ import annotations

import pytest

from fno.constants import HEALTH_LATE, HEALTH_MISSED, HEALTH_NOT_DUE, HEALTH_OK
from fno.health.model import Deadline, EvidenceUnknown
from fno.health.preopen_checks import PreopenCheck
from fno.preopen.day_row import PREOPEN_RECEIPT_BY, receipt_path

from .fakes import DAY, Repo, ist


@pytest.fixture
def repo(tmp_path):
    return Repo(tmp_path)


def _check(repo):
    return PreopenCheck(repo.evidence, Deadline(PREOPEN_RECEIPT_BY))


def _pushed(repo, at):
    path = repo.write(receipt_path(DAY), "digest\t10\t2026-10-15T03:41:00+00:00\tpreopen\trun\n")
    repo.receipts.file(path, at)


def test_the_receipt_path_is_the_day_rows_receipt():
    assert receipt_path(DAY) == "receipts/data/preopen/day/2026/10/2026-10-15.csv.sha256"


@pytest.mark.parametrize(("pushed", "status"), [(ist(DAY, 9, 15), HEALTH_OK), (ist(DAY, 9, 15, 1), HEALTH_LATE)])
def test_on_time_by_its_push_up_to_0915_exactly(repo, pushed, status):
    _pushed(repo, pushed)
    assert _check(repo).check(DAY, ist(DAY, 17, 51)).status == status


@pytest.mark.parametrize(("now", "status"), [(ist(DAY, 9, 14, 59), HEALTH_NOT_DUE), (ist(DAY, 9, 15), HEALTH_MISSED)])
def test_no_receipt_is_not_due_before_0915_then_missed(repo, now, status):
    result = _check(repo).check(DAY, now)
    assert result.status == status and "never ran" in result.detail


def test_a_receipt_whose_push_time_is_unknown_is_unknown_never_ok(repo):
    repo.write(receipt_path(DAY), "digest\n")  # committed, but no push receipt found
    with pytest.raises(EvidenceUnknown):
        _check(repo).check(DAY, ist(DAY, 17, 51))


def test_expected_on_regular_and_special_sessions_only_once_live():
    from dataclasses import replace

    from fno.config import load_app_config
    from fno.health.wiring import build_health_check

    row = next(e for e in build_health_check(load_app_config()).expectations if e.name == "A22 pre-open data")
    assert not row.expected_on(DAY, "regular")  # live_from None until the first live morning
    live = replace(row, live_from=DAY)
    assert [live.expected_on(DAY, kind) for kind in ("regular", "special", "holiday", "muhurat")] == [
        True, True, False, False]  # fmt: skip
