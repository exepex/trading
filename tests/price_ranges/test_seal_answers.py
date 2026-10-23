"""Story receipts-reach, the seal side: a seal is stored only on an answer. A failed evidence read is retried within
the run and never becomes a stored "late"; no push by the deadline and a log that no longer reaches the push are final,
each named. G13b's 15:45 deadline and G13d's same-day 15:30 one behave alike (the G13 builder's request)."""

import json
from datetime import datetime, time, timedelta

import pytest

from fno.health.model import EvidenceNotCommitted, EvidenceNotPushed, EvidenceOutsideLog
from fno.models import IST
from fno.premium_ranges.folders import live_path as premium_live_path
from fno.premium_ranges.folders import seal_path as premium_seal_path
from fno.premium_ranges.wiring import same_day_close
from fno.price_ranges.reader import receipt_file
from fno.price_ranges.sealing import NOT_YET, UNAVAILABLE, SealCheck
from fno.price_ranges.seals import Seals
from tests.price_distribution.builders import DAY, drive_store
from tests.price_ranges.builders import CALENDAR

G13B = {"deadline_of": None, "paths": {}}
G13D = {"deadline_of": same_day_close, "paths": {"live_path_of": premium_live_path, "seal_path_of": premium_seal_path}}
SIDES = pytest.mark.parametrize("side", [G13B, G13D], ids=["G13b", "G13d"])


def at_16(days_after: int) -> datetime:
    return datetime.combine(DAY + timedelta(days=days_after), time(16), IST)


class Evidence:
    """Push evidence that answers with `failures` in order, then `last` for every later read."""

    def __init__(self, *failures, last=None):
        self.failures, self.last, self.reads = list(failures), last, 0

    def __call__(self, path):
        self.reads += 1
        answer = self.failures.pop(0) if self.failures else self.last
        if isinstance(answer, Exception):
            raise answer
        return answer


def seals(tmp_path, side, evidence, now, attempts=1, pauses=None):
    store, drive, _ = drive_store(tmp_path)
    pause = (pauses if pauses is not None else []).append
    check = SealCheck(evidence, CALENDAR, side["deadline_of"], lambda: now, attempts, pause)
    return Seals(check, store, receipt_file, lambda: now, **side["paths"]), drive


@SIDES
def test_a_failed_read_is_retried_within_the_run_and_then_seals(tmp_path, side):
    pushed, pauses = datetime.combine(DAY, time(15, 0), IST), []
    evidence = Evidence(OSError("activity log not reached"), RuntimeError("HTTP 502"), last=pushed)
    found, drive = seals(tmp_path, side, evidence, at_16(1), attempts=3, pauses=pauses)
    assert "seal stored (sealed at" in found.record("NIFTY", DAY, "1545")
    assert evidence.reads == 3 and pauses == [10, 10] and len(drive.files) == 1


@SIDES
def test_an_unreadable_evidence_stays_open_and_is_never_stored_late(tmp_path, side):
    found, drive = seals(tmp_path, side, Evidence(last=OSError("activity log not reached")), at_16(7))
    assert "seal pending" in found.record("NIFTY", DAY, "1545") and not drive.files
    after, drive = seals(tmp_path / "b", side, Evidence(last=OSError("activity log not reached")), at_16(8))
    line = after.record("NIFTY", DAY, "1545")
    assert "seal NOT recorded, its evidence unreadable for 7 days" in line and not drive.files
    assert after.seal("NIFTY", DAY, "1545").waiting == UNAVAILABLE  # readers still compute it, never a stored late


@SIDES
def test_no_push_by_the_deadline_is_final_and_named(tmp_path, side):
    monday = at_16(3)  # DAY is a Friday: G13b's deadline is Monday 09:15, G13d's Friday 15:30
    found, drive = seals(tmp_path, side, Evidence(last=EvidenceNotPushed("no push of abc in the log")), monday)
    assert "seal stored (late)" in found.record("NIFTY", DAY, "1545")
    stored = json.loads(next(iter(drive.files.values())))
    assert stored["late"] and stored["reason"].startswith("late: no push of it by the deadline")


def test_no_push_yet_before_the_deadline_stays_open(tmp_path):
    before = datetime.combine(DAY, time(15, 50), IST)  # G13b's deadline is the next session's 09:15
    check = SealCheck(Evidence(last=EvidenceNotPushed("no push yet")), CALENDAR, now=lambda: before)
    assert check.seal("receipts/x.sha256", DAY).waiting == NOT_YET


@SIDES
def test_a_push_older_than_the_log_is_final_and_named_apart(tmp_path, side):
    found, drive = seals(tmp_path, side, Evidence(last=EvidenceOutsideLog("the log ends at 2026-10-11")), at_16(2))
    assert "seal stored (late)" in found.record("NIFTY", DAY, "1545")
    stored = json.loads(next(iter(drive.files.values())))
    assert stored["reason"].startswith("late: GitHub's activity log no longer reaches its push")


def test_an_answer_is_never_retried(tmp_path):
    evidence, pauses = Evidence(last=EvidenceNotCommitted("no commit adding it")), []
    check = SealCheck(evidence, CALENDAR, now=lambda: at_16(1), attempts=3, pause=pauses.append)
    assert check.seal("receipts/x.sha256", DAY).waiting == NOT_YET and evidence.reads == 1 and pauses == []
