"""Judge 84 (E5): an open Book 1 trade's time exit is fixed at its decision. It is read from the committed run (the
version file as the run read it, the expiry in the opportunity ID), so an edit to today's version file, a file that no
longer parses, or an unrelated broken draft never stops or moves it; today's file only feeds the alerts."""

import json
import subprocess
from datetime import date, datetime, time

import pytest

from fno.books import book1_exits
from fno.books.book1_exits import PlaybookExitRules
from fno.books.book1_records import DecidedExits, decided_exit_days
from fno.books.book1_wiring import build_book1_exit_rules
from fno.constants import BOOK1_RULES, PLAYBOOK_FOLDER
from fno.desk.exit_rules import ExitContext
from fno.desk.pricing import DeskLeg
from fno.desk.status import OpenPosition
from fno.models import IST
from fno.playbook.decision_store import DecisionStore
from fno.playbook.opportunities import OpportunityFinder
from fno.playbook.schema import parse_strategy
from fno.research_engine.cycles import TradingDays
from fno.research_engine.structures import BOUGHT, Leg
from tests.checks.builders import CALENDAR
from tests.decisions.builders import snapshot

from .builders import EXITS, book1, book1_doc, clock_at
from .openings import open_trades

DAY = date(2026, 10, 13)
FINDER = OpportunityFinder(TradingDays(CALENDAR))
SUMS_AT = {}


def sums_at(path, commit):
    return SUMS_AT["at"](path, commit)


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "sent"


@pytest.fixture
def decided(tmp_path, monkeypatch):
    """Book 1 decides 13 Oct (one chosen trade); its open position is the decided trade."""
    decider, commits = book1(tmp_path, snapshot(book1_doc()), clock_at(datetime.combine(DAY, time(15), IST)))
    decider.decide(DAY)
    [run] = DecisionStore(tmp_path, BOOK1_RULES).runs(DAY)
    open_trades(tmp_path, BOOK1_RULES, DAY, run.name, commits.made[0][0])  # story D3b: only filled trades count
    SUMS_AT["at"] = commits.committed_bytes
    [(trade_id, (exit_day, version))] = decided_exit_days(tmp_path, BOOK1_RULES, FINDER, sums_at).exits.items()
    legs = ((DeskLeg("N", date(2026, 11, 27), Leg(25_000, "CE", BOUGHT)), 65),)
    position = OpenPosition(trade_id, version, "d", legs, 0.0, datetime(2026, 10, 13, 15, 15), "exec", "", ())
    monkeypatch.setattr(book1_exits, "open_positions", lambda records: [position])
    return tmp_path, trade_id, exit_day, version


def commit_for_real(root):
    """The real wiring asks real git for the run's committed sums file: commit the run, and name that commit in the
    run log as E3 would have."""
    for args in (("init", "-q"), ("config", "user.email", "t@example.org"), ("config", "user.name", "t"),
                 ("config", "core.hooksPath", "/dev/null"), ("add", "-A"), ("commit", "-q", "-m", "run")):  # fmt: skip
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    log = root / "journal" / "runs" / f"{DAY}.json"
    body = json.loads(log.read_text())
    body["steps"]["decisions"]["result"][BOOK1_RULES]["commit"] = head.stdout.strip()
    log.write_text(json.dumps(body))


def rules(root, version_text, alerts):
    decided = lambda book: decided_exit_days(root, book, FINDER, sums_at)  # noqa: E731
    exits = PlaybookExitRules(decided, version_text, lambda b: None, alerts)
    return exits.rules(BOOK1_RULES)


def test_the_exit_is_the_one_d2_fixed_at_the_decision(decided):
    root, trade, exit_day, version = decided
    expiry = date.fromisoformat(trade.rsplit(":", 1)[1])  # D2's trade ID ends with the opportunity's expiry
    assert version == "sc-a-v1" and exit_day == FINDER.exit_day(parse_strategy(book1_doc()), expiry)
    [rule] = rules(root, lambda v: None, Alerts())[trade]
    assert rule.exit_day == exit_day and rule.reached(None, ExitContext(exit_day, None))


def test_an_edited_or_unreadable_version_file_never_moves_or_stops_the_exit(decided):
    root, trade, exit_day, _ = decided
    for text in ("{ not yaml", "", None):  # unreadable, empty, deleted: alert only
        alerts = Alerts()
        [rule] = rules(root, lambda v, text=text: text, alerts)[trade]
        assert rule.exit_day == exit_day and len(alerts.sent) == 1 and "cannot be read now" in alerts.sent[0]
    moved = book1_doc(structure={**book1_doc()["structure"], "expiry": {**book1_doc()["structure"]["expiry"],
                                                                         "exit_days_before_expiry": 5}})  # fmt: skip
    import yaml

    [rule] = rules(root, lambda v: yaml.safe_dump(moved), Alerts())[trade]
    assert rule.exit_day == exit_day  # a later edit to the version file is a new version, never this trade's exit


def test_a_stop_stated_in_today_s_file_alerts_and_the_decided_time_exit_still_runs(decided):
    import yaml

    root, trade, exit_day, _ = decided
    stop = book1_doc(exits={**EXITS, "loss": "none until day 10, then stop at 2x credit"})
    alerts = Alerts()
    [rule] = rules(root, lambda v: yaml.safe_dump(stop), alerts)[trade]
    assert rule.exit_day == exit_day and "stop at 2x credit" in alerts.sent[0] and "still runs" in alerts.sent[0]


def test_an_unrelated_broken_draft_leaves_every_exit_applied(decided):
    """Through the real wiring: only the trade's own version file is ever read, and only for the alert."""
    root, trade, exit_day, _ = decided
    folder = root / PLAYBOOK_FOLDER
    folder.mkdir(exist_ok=True)
    (folder / "draft-v1.yaml").write_text("name: [unclosed")  # a draft that does not parse
    commit_for_real(root)
    [rule] = build_book1_exit_rules(root).rules(BOOK1_RULES)[trade]
    assert rule.exit_day == exit_day


def test_a_trade_without_a_committed_record_is_left_to_e4_with_an_alert(decided):
    alerts = Alerts()
    exits = PlaybookExitRules(lambda book: DecidedExits({}, {}, {}), lambda v: None, lambda b: None, alerts)
    assert exits.rules(BOOK1_RULES) == {} and "no committed decision record" in alerts.sent[0]
