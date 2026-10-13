"""The owner's conditions on `sealed_same_day` isolation (14 Oct 2026; judge 62): every record carries the label; each
audited session has one written-once audit record; a planted breach makes that book-day unscored for the scorer; a
selected but unaudited day stays pending; two breaches in 20 session days stop that book's fires with a #fno-desk line,
and a new version starts clean; the audit draw is every session of the first 10 days, then 2 a week, fixed per week."""

import json
import shutil
from datetime import date, datetime, timedelta

import pytest

from fno.ai.audit_plan import FiredSession, audits_due, sessions_to_audit
from fno.ai.fire import AiBookFirer
from fno.ai.paths import fired_path, pack_path, rules_path
from fno.ai.scoring_gate import PENDING, SCORED, UNSCORED, scoring_status
from fno.ai.stop_rule import stop_reason
from fno.ai.transcript_audit import AuditRefused, TranscriptAudits, new_audit
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.models import IST
from tests.ai.fakes import DAY, Clock, at
from tests.ai.test_fire_and_collect import Desk

NOW = datetime(2026, 10, 14, 16, 0, tzinfo=IST)
LATER = date(2026, 12, 1)  # weeks after DAY: every week drawn


@pytest.fixture
def desk(tmp_path):
    desk = Desk(tmp_path)
    desk.fire()
    desk.answer(BOOK2_HYBRID)
    desk.answer(BOOK3_AI)
    desk.collect()
    return desk


def audit(desk, book, day=DAY, breaches=()):
    fired = json.loads((desk.root / fired_path(day)).read_text())[book]
    record = new_audit(day, book, fired, list(breaches), "read the session's tool calls", "judge", NOW)
    return TranscriptAudits(desk.root).record(day, record)


def test_every_record_carries_the_isolation_label(desk):
    for book in (BOOK2_HYBRID, BOOK3_AI):
        versions = {r.record.method_or_version for r in desk.records(book).values()}
        assert len(versions) == 1 and versions.pop().endswith("/isolation:sealed_same_day")
        assert desk.audit(book)["isolation"] == "sealed_same_day"


def test_an_audit_is_written_once_and_a_breach_must_name_its_kind(desk):
    assert audit(desk, BOOK3_AI).endswith("2026-10-13_book3_ai_transcript_audit.json")
    with pytest.raises(AuditRefused, match="written once"):
        audit(desk, BOOK3_AI, breaches=["ran_forecast_code"])
    fired = json.loads((desk.root / fired_path(DAY)).read_text())[BOOK2_HYBRID]
    with pytest.raises(AuditRefused, match="unknown breach"):
        new_audit(DAY, BOOK2_HYBRID, fired, ["peeked"], "x", "judge", NOW)
    with pytest.raises(AuditRefused, match="not fired"):
        new_audit(DAY, BOOK2_HYBRID, {"fired": False}, [], "x", "judge", NOW)


def test_a_planted_breach_makes_the_day_unscored_and_a_due_audit_keeps_it_pending(desk):
    assert scoring_status(desk.root, DAY, BOOK2_HYBRID, LATER).status == PENDING  # first 10 days: audit due
    audit(desk, BOOK2_HYBRID, breaches=["read_other_records"])
    audit(desk, BOOK3_AI)
    breached, clean = (scoring_status(desk.root, DAY, b, LATER) for b in (BOOK2_HYBRID, BOOK3_AI))
    assert breached.status == UNSCORED and "read_other_records" in breached.reason
    assert clean.status == SCORED and clean.isolation == "sealed_same_day"
    assert audits_due(desk.root, LATER) == []


def test_a_late_day_is_unscored_whatever_its_audit(tmp_path):
    desk = Desk(tmp_path)
    desk.fire()
    desk.answer(BOOK3_AI, sealed=datetime(2026, 10, 13, 15, 15, 1, tzinfo=IST))
    desk.collect()
    assert scoring_status(desk.root, DAY, BOOK3_AI, LATER).status == UNSCORED


def plant_days(desk, days):
    """More session days with the same pack and a fire log each (what earlier days' runs leave in the repository)."""
    for day in days:
        (desk.root / pack_path(day)).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(desk.root / pack_path(DAY), desk.root / pack_path(day))
        rules = (desk.root / rules_path(DAY)).read_text().replace(DAY.isoformat(), day.isoformat())
        (desk.root / rules_path(day)).write_text(rules)
        log = json.loads((desk.root / fired_path(DAY)).read_text())
        (desk.root / fired_path(day)).write_text(json.dumps(log))


def test_two_breaches_in_20_session_days_stop_the_books_fires_and_a_new_version_starts_clean(desk):
    earlier = [DAY - timedelta(days=n) for n in (7, 6, 5)]
    plant_days(desk, earlier)
    audit(desk, BOOK3_AI, earlier[0], ["network_beyond_pushes"])
    audit(desk, BOOK3_AI, earlier[1], ["file_outside_input"])
    audit(desk, BOOK2_HYBRID, earlier[0], ["ran_forecast_code"])  # one breach: Hybrid keeps firing
    following = DAY + timedelta(days=1)
    plant_days(desk, [following])
    (desk.root / fired_path(following)).unlink()
    for trigger in desk.triggers.values():
        trigger.fired.clear()
    AiBookFirer(desk.root, desk.triggers, desk.alerts, Clock(at(15, 10))).fire(following)
    assert desk.triggers[BOOK3_AI].fired == [] and len(desk.triggers[BOOK2_HYBRID].fired) == 1
    assert "book3_ai not fired: stopped: 2 transcript breaches in 20 session days" in desk.alerts.lines[-1]
    log = json.loads((desk.root / fired_path(following)).read_text())
    assert not log[BOOK3_AI]["fired"] and log[BOOK3_AI]["reason"].startswith("stopped")

    assert stop_reason(desk.root, BOOK3_AI, "book3_ai/v2/sha256:" + "0" * 64 + "/isolation:sealed_same_day",
                       following) == ""  # fmt: skip


def sessions(days, books=(BOOK2_HYBRID, BOOK3_AI)):
    return [FiredSession(d, b, {"fired": True}) for d in days for b in books]


def test_the_first_10_days_are_all_audited_then_2_a_week_drawn_once_the_week_is_over():
    days = [
        date(2026, 10, 14) + timedelta(days=n)
        for n in range(30)
        if (date(2026, 10, 14) + timedelta(days=n)).weekday() < 5
    ]
    fired = sessions(days)
    first = {s.day for s in sessions_to_audit(fired, days[9])}
    assert first == set(days[:10])
    later = sessions_to_audit(fired, date(2026, 12, 1))
    by_week = {}
    for s in later:
        if s.day not in days[:10]:
            by_week.setdefault(s.day.isocalendar()[:2], []).append(s)
    assert by_week and all(len(chosen) == 2 for chosen in by_week.values())
    assert later == sessions_to_audit(list(reversed(fired)), date(2026, 12, 1))  # fixed by the week, not the order
    open_week = sessions_to_audit(fired, days[-1])
    assert all(s.day.isocalendar()[:2] < days[-1].isocalendar()[:2] or s.day in days[:10] for s in open_week)
