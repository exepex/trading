"""Story F1t criterion 2: each live book fired once with exactly its own pointer, or `not_fired` with the first reason
that applies; the fire log committed before any trigger call; a rerun fires nothing."""

import json

import pytest

from fno.ai.fire_once import FIRED, NOT_FIRED
from fno.ai.transcript_audit import TranscriptAudit, TranscriptAudits
from fno.ai_trading.fire import DecisionFirer
from fno.ai_trading.paths import fired_path, transcript_audit_path
from fno.ai_trading.pointer import MAX_POINTER_BYTES, parse_pointer
from fno.ai_trading.ports import DayPacks, NoAnalystCards
from fno.composition import build_record_scanner
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.desk.private_pack import PrivatePack
from fno.learning.writer import BudgetSignal
from fno.pipeline.trigger import FireFailed, RoutineTrigger
from tests.ai.fakes import Clock

from .builders import CARDS, DAY, at, common_pack, private_body, registry

BOOKS = (BOOK2_HYBRID, BOOK3_AI)


class Trigger(RoutineTrigger):
    def __init__(self, fail=""):
        self.fail, self.sent = fail, []

    def fire(self, pointer):
        if self.fail:
            raise FireFailed(self.fail)
        self.sent.append(pointer.to_text())
        return f"https://example.invalid/{pointer.book}"


class Budget(BudgetSignal):
    def __init__(self, stopped=False):
        self.stopped = stopped

    def ai_roles_stopped(self, day):
        return self.stopped


class Cards:
    def item(self, day, units):
        return CARDS


def firer(tmp_path, now=None, triggers=None, budget=False, packs=None, reg=None, commits=None, body=None):
    commits, now = ([] if commits is None else commits), now or at(15, 1)
    triggers = triggers or {book: Trigger() for book in BOOKS}
    packs = packs or DayPacks(lambda day: common_pack(day),
                              lambda book, day: PrivatePack(book, day, body or private_body(book, day)))  # fmt: skip
    record = lambda paths, message: commits.append(message)  # noqa: E731
    built = DecisionFirer(tmp_path, reg or registry(tmp_path), triggers, Budget(budget), packs, Cards(),
                          build_record_scanner(), record, Clock(now))  # fmt: skip
    return built, triggers, commits


def fire(tmp_path, books=BOOKS, **kwargs):
    built, triggers, commits = firer(tmp_path, **kwargs)
    return built.fire(DAY, books, registry(tmp_path).versions and _timing()), triggers, commits


def _timing():
    from fno.ai_trading.fire import FireTiming

    return FireTiming(at(15, 7), at(15, 10), at(15, 10, 10))


def test_each_live_book_is_fired_once_with_its_own_pointer(tmp_path):
    log, triggers, commits = fire(tmp_path)
    assert [log[b]["state"] for b in BOOKS] == [FIRED, FIRED] and len(commits) == 1
    for book in BOOKS:
        (text,) = triggers[book].sent
        sent = parse_pointer(text, registry(tmp_path))
        assert sent.book == book and sent.private_pack == private_body(book) and sent.analyst_cards == CARDS
        assert log[book]["labels"]["private_pack_sha256"] == sent.private_pack_sha256
        assert log[book]["session"] == f"https://example.invalid/{book}"
    assert "cash_ledger" not in json.dumps(log) and "IV rich" not in json.dumps(log)  # no pack, no card text


def test_a_rerun_fires_nothing(tmp_path):
    built, triggers, commits = firer(tmp_path)
    first = built.fire(DAY, BOOKS, _timing())
    assert built.fire(DAY, BOOKS, _timing()) == first
    assert [len(t.sent) for t in triggers.values()] == [1, 1] and len(commits) == 1


def not_fired(log, book=BOOK2_HYBRID):
    assert log[book]["state"] == NOT_FIRED
    return log[book]["reason"]


def test_budget_stop(tmp_path):
    assert "budget" in not_fired(fire(tmp_path, budget=True)[0])


def test_no_registered_version(tmp_path):
    log = fire(tmp_path, reg=registry(tmp_path, books=(BOOK3_AI,)))[0]
    assert "no registered decision version" in not_fired(log) and log[BOOK3_AI]["state"] == FIRED


def test_the_stop_rule_counts_breaches_of_this_version_in_decision_days(tmp_path):
    version = registry(tmp_path).current(BOOK2_HYBRID).label
    audits = TranscriptAudits(tmp_path, transcript_audit_path)
    for day_number, label in ((14, version), (15, "older"), (16, version)):
        day = DAY.replace(day=day_number)
        (tmp_path / fired_path(day)).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / fired_path(day)).write_text("{}")
        audits.record(day, TranscriptAudit(BOOK2_HYBRID, day.isoformat(), label, "s", "breach", ["file_outside_input"],
                                           "read journal/book3_ai", "judge", "2026-10-17"))  # fmt: skip
    assert "stopped: 2 transcript breaches" in not_fired(fire(tmp_path)[0])


def test_one_breach_still_fires(tmp_path):
    day = DAY.replace(day=16)
    (tmp_path / fired_path(day)).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / fired_path(day)).write_text("{}")
    version = registry(tmp_path).current(BOOK2_HYBRID).label
    TranscriptAudits(tmp_path, transcript_audit_path).record(
        day,
        TranscriptAudit(
            BOOK2_HYBRID, day.isoformat(), version, "s", "breach", ["file_outside_input"], "e", "judge", "2026-10-17"
        ),
    )
    assert fire(tmp_path)[0][BOOK2_HYBRID]["state"] == FIRED


def test_no_packs(tmp_path):
    def missing(book, day):
        raise FileNotFoundError("journal/book2_hybrid/packs/2026-10-19/private.json")

    log = fire(tmp_path, packs=DayPacks(lambda day: common_pack(day), missing))[0]
    assert "packs are not written" in not_fired(log)


@pytest.mark.parametrize("now, fired", [(at(15, 7), True), (at(15, 7, 1), False)])
def test_a_start_after_latest_fire_fires_nothing(tmp_path, now, fired):
    log = fire(tmp_path, now=now)[0]
    assert (log[BOOK2_HYBRID]["state"] == FIRED) is fired
    if not fired:
        assert "after 15:07:00" in log[BOOK2_HYBRID]["reason"]


def test_a_pointer_over_the_cap_is_not_sent(tmp_path):
    body = private_body()
    body["files"][1]["text"] += "x" * MAX_POINTER_BYTES
    reason = not_fired(fire(tmp_path, books=(BOOK2_HYBRID,), body=body)[0])
    assert "over the 65536-byte cap" in reason


def test_a_pointer_the_record_scan_flags_is_not_sent_even_inside_an_escaped_file_text(tmp_path):
    body = private_body()
    body["files"][0]["text"] += "\napi_key: s3cr3tvalue123456\n"
    assert "public-record scan flags" in not_fired(fire(tmp_path, books=(BOOK2_HYBRID,), body=body)[0])


def test_a_trigger_failure_is_not_fired_with_its_reason(tmp_path):
    log = fire(tmp_path, triggers={BOOK2_HYBRID: Trigger("HTTP 429"), BOOK3_AI: Trigger()})[0]
    assert not_fired(log) == "HTTP 429" and log[BOOK3_AI]["state"] == FIRED


def test_no_cards_source_gives_an_item_with_no_roles():
    assert NoAnalystCards().item(DAY, ("analyst_volatility",))["roles"] == []
