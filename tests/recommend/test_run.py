"""REC1b criteria 9 and 10: the record is saved write-once with its receipt pushed before any post; a failed push
posts no recommendation, only one problem line; a changed rung rule makes no record; the #fno-desk line says it is
the recommender's, carries no strike, price or strategy internal, and names an unavailable source."""

import json
import re
import shutil
from dataclasses import replace

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


def test_a_different_answer_for_a_recorded_day_is_refused_and_alerted():
    run, data, publisher, alerts = runner()
    run.run(DAY)
    run.ports = replace(PORTS, conditions=FakeConditions(fails="log gone"))
    result = run.run(DAY)
    assert not result.ok and "a different recommendation is already recorded" in alerts.lines[-1]


def test_an_unavailable_school_is_named_in_the_line():
    ports = replace(PORTS, sources=(PORTS.sources[0], FakeSource(CandidateSourceName.SCHOOL, status="ok (school:OFF)")))
    run, *_, alerts = runner(ports=ports)
    run.run(DAY)
    assert "school: unavailable (ok (school:OFF))" in alerts.lines[0]


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
