"""REC1b criteria 9 and 10: the record is saved write-once with its receipt pushed before any post; a failed push
posts no recommendation, only one problem line; a changed rung rule makes no record; the #fno-desk line says it is
the recommender's, carries no strike, price or strategy internal, and names an unavailable source."""

import hashlib
import json
import re
import shutil
from dataclasses import replace
from datetime import timedelta

from fno.recommend.constants import CandidateSourceName
from fno.recommend.gather import Header, Ports
from fno.recommend.run import RecommendRun
from fno.recommend.rungs import RUNG_RULE_PATH
from fno.recommend.store import DriveRecommendations, record_path
from tests.recommend.builders import DAY, MADE_AT
from tests.recommend.fakes import (
    FakeConditions,
    FakeData,
    FakeEligibility,
    FakeEvidence,
    FakePublisher,
    FakeSource,
    RecordingAlerts,
    seen,
)
from tests.recommend.test_rung_rule_card import ROOT

CS1, DESK = "school:CS1@1", "book1_rules"
PORTS = Ports(
    sources=(FakeSource(CandidateSourceName.DESK_BOOK1, (seen(DESK),)),
             FakeSource(CandidateSourceName.SCHOOL, (seen(CS1, True, road="#NIFTY-M"),))),
    evidence=FakeEvidence(rated=(CS1, DESK)), conditions=FakeConditions(), eligibility=FakeEligibility(),
)  # fmt: skip


def runner(root=ROOT, ports=PORTS, fails=False):
    data, alerts = FakeData(), RecordingAlerts()
    publisher = FakePublisher(data, fails=fails)
    run = RecommendRun(root, ports, DriveRecommendations(data, publisher), alerts,
                       lambda: Header("c" * 40, "d" * 64), lambda: MADE_AT)  # fmt: skip
    return run, data, publisher, alerts


def test_today_the_line_says_do_not_trade_and_no_established_version():
    run, data, publisher, alerts = runner()
    result = run.run(DAY)
    assert result.ok and len(alerts.lines) == 1
    line = alerts.lines[0]
    assert line.startswith(f"PAPER ONLY. Recommender (not the card) for {DAY:%d %b %Y}.")
    assert "Real money: DO NOT TRADE (no version has passed" in line
    assert "Paper: NO TRADE (no_established_version" in line
    assert "Candidates: desk:book1: 1 candidate(s); school: 1 candidate(s)." in line
    assert "Paper, not a recommendation: 1 trade(s) of versions below rung 3." in line
    assert record_path(DAY) in data.files and f"data/{record_path(DAY)}" in publisher.pushed


def test_the_line_carries_no_strike_price_or_internal():
    run, *_, alerts = runner()
    run.run(DAY)
    line = alerts.lines[0]
    assert not re.search(r"\b\d{4,6}\s*(CE|PE|call|put)\b|Rs\s*\d|strike|premium|delta", line, re.IGNORECASE)


def test_the_receipt_is_pushed_before_the_line_is_posted():
    run, data, publisher, alerts = runner()
    calls = []
    original_send = alerts.send
    alerts.send = lambda text: calls.append(("post", bool(publisher.pushed))) or original_send(text)
    run.run(DAY)
    assert calls == [("post", True)]


def test_a_refused_push_posts_no_recommendation_only_the_problem_line():
    """Criterion 9's plant: the push fails, nothing of the recommendation is posted."""
    run, data, publisher, alerts = runner(fails=True)
    result = run.run(DAY)
    assert not result.ok
    assert alerts.lines == [f"recommendation NOT posted for {DAY}: {record_path(DAY)}: RuntimeError"]


def test_the_same_day_again_with_the_same_answer_changes_nothing():
    run, data, publisher, alerts = runner()
    run.run(DAY)
    before = dict(data.files)
    assert run.run(DAY).ok and data.files == before


def test_a_recorded_day_is_never_written_again_and_its_own_line_is_re_sent():
    """Judge 654 m1: a run that pushed the receipt and stopped before its post loses no line; the rerun re-sends the
    stored record's own line, labelled, and never the new answer."""
    run, data, publisher, alerts = runner()
    run.run(DAY)
    before, first_line = dict(data.files), alerts.lines[0]
    run.ports = replace(PORTS, conditions=FakeConditions(fails="log gone"))  # another answer now: it must not land
    result = run.run(DAY)
    assert result.ok and data.files == before and len(alerts.lines) == 2
    resent = alerts.lines[1]
    assert "Re-sent: this day was already recorded (receipt eeeeeeeeeeee)" in resent
    assert "no_established_version" in resent and "data_check_failed" not in resent
    assert resent.split(" Re-sent:")[0] == first_line.split(" Record ")[0]


def test_a_save_stopped_before_its_push_is_adopted_by_the_next_run():
    """The review's case: Drive written, push refused; the next run receipts and posts the first record."""
    run, data, publisher, alerts = runner(fails=True)
    assert not run.run(DAY).ok and record_path(DAY) in data.files
    first = data.files[record_path(DAY)]
    publisher.fails = False
    run.clock = lambda: MADE_AT + timedelta(minutes=7)  # a rerun makes other bytes; the first record stands
    result = run.run(DAY)
    assert result.ok and data.files[record_path(DAY)] == first
    assert (
        "This is the record made at 09:50 UTC, whose save stopped before its push, now receipted." in alerts.lines[-1]
    )
    assert alerts.lines[-1].endswith(f"Record {record_path(DAY)}, SHA-256 {hashlib.sha256(first).hexdigest()[:12]}.")


def test_bytes_on_drive_that_are_not_the_day_s_record_are_never_written_over():
    run, data, publisher, alerts = runner()
    data.files[record_path(DAY)] = b'{"planted": true}'
    result = run.run(DAY)
    assert not result.ok and data.files[record_path(DAY)] == b'{"planted": true}'
    assert "not its record" in alerts.lines[0] and publisher.pushed == {}


def test_an_unavailable_school_is_named_in_the_line():
    ports = replace(PORTS, sources=(PORTS.sources[0], FakeSource(CandidateSourceName.SCHOOL, status="ok, school:OFF")))
    run, *_, alerts = runner(ports=ports)
    run.run(DAY)
    assert "school: unavailable (ok, school:OFF)" in alerts.lines[0]


def test_an_input_problem_is_alerted_beside_the_line_and_fails_the_step():
    run, *_, alerts = runner(ports=replace(PORTS, conditions=FakeConditions(fails="log gone")))
    result = run.run(DAY)
    assert not result.ok
    assert "Paper: NO TRADE (data_check_failed" in alerts.lines[0]
    assert (
        alerts.lines[1] == f"recommendation for {DAY}, input problem: the day's conditions could not be read: log gone"
    )


def test_a_changed_rung_rule_makes_no_record(tmp_path):
    (tmp_path / RUNG_RULE_PATH).parent.mkdir(parents=True)
    shutil.copy(ROOT / RUNG_RULE_PATH, tmp_path / RUNG_RULE_PATH)
    with open(tmp_path / RUNG_RULE_PATH, "a") as card:
        card.write("\n| watching_sessions | 25 |\n")
    run, data, publisher, alerts = runner(root=tmp_path)
    result = run.run(DAY)
    assert not result.ok and data.files == {} and "not the pinned rung rule" in alerts.lines[0]


def test_the_saved_record_is_the_decided_one():
    run, data, *_ = runner()
    run.run(DAY)
    saved = json.loads(data.files[record_path(DAY)])
    assert (saved["reason"], saved["real_money"]) == ("no_established_version", "do_not_trade_real_money")
