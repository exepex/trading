"""Story O1 fix (found by O2's end-to-end day, 16 Oct): A4's recorder refuses a start more than 20 minutes before its
14:55 window and records nothing, so the run starts each 3 pm part no earlier than A4's own earliest start, from any of
its waits, a command's included, and never runs git to do it."""

from datetime import date, datetime, time, timedelta

from fno.daily.quote_parts import EARLIEST_START, QUOTE_PARTS, QuoteParts
from fno.models import IST
from fno.quotes.recorder import MAX_EARLY_WAIT_SECONDS, WINDOW_START, QuoteSnapshotRecorder
from fno.storage.raw_store import LocalFolderStore
from tests.quotes.test_quote_recorder import FakeProvider
from tests.timetable.fakes import Clock

from .fakes import FakeProcesses, RecordingCommitter

DAY = date(2026, 10, 14)


def _at(hour, minute):
    return datetime(2026, 10, 14, hour, minute, tzinfo=IST)


def test_the_earliest_start_is_inside_a4_s_early_limit_with_its_margin():
    window = datetime.combine(DAY, WINDOW_START, IST)
    earliest = datetime.combine(DAY, EARLIEST_START, IST)
    assert time(14, 38) == EARLIEST_START and timedelta(0) < window - earliest < timedelta(
        seconds=MAX_EARLY_WAIT_SECONDS
    )


def test_a4_s_recorder_records_nothing_when_started_at_the_routine_s_14_33_but_waits_from_the_earliest_start(tmp_path):
    """The bug itself, on A4's real recorder: from 14:33 it is "too early" at once; from EARLIEST_START it waits for
    the window and tries (the fake's quotes are a day old, so A4's own rule then calls the day closed)."""
    clock = Clock()
    clock.now = _at(14, 33)
    early = QuoteSnapshotRecorder(FakeProvider(), LocalFolderStore(tmp_path / "early"), clock, clock.advance).record()
    assert early.status == "too early" and clock.now == _at(14, 33)
    clock.now = datetime.combine(DAY, EARLIEST_START, IST)
    waited = QuoteSnapshotRecorder(FakeProvider(), LocalFolderStore(tmp_path / "ok"), clock, clock.advance).record()
    assert waited.status != "too early" and clock.now >= datetime.combine(DAY, WINDOW_START, IST)


def test_a_part_is_never_started_before_its_time_and_starts_from_any_wait_without_git():
    clock = Clock()
    clock.now = _at(14, 33)
    processes = FakeProcesses(clock, {p.arguments: (_at(15, 0), 0, []) for p in QUOTE_PARTS})
    commits, changed = [], []
    parts = QuoteParts(QUOTE_PARTS, processes, RecordingCommitter(clock, commits), changed.append, None, clock)
    assert parts.start(DAY) == ["nifty", "nse"] and processes.started == []  # the day is open, nothing started
    clock.now = _at(14, 37)
    parts.start_due()
    assert processes.started == []
    clock.now = _at(14, 38)
    parts.start_due()  # what a command's wait calls: starts, never commits (no git while a command runs)
    assert [args for _, args in processes.started] == [QUOTE_PARTS[0].arguments, QUOTE_PARTS[1].arguments]
    assert commits == [] and changed == []
    parts.start_due()
    assert len(processes.started) == 2  # once


def _command_steps(step):
    """Every `CommandStep` inside a built O1 step (through `Alerted`, `LiveFrom` and `NotBefore`)."""
    from fno.daily.steps import CommandStep

    while not isinstance(step, CommandStep) and hasattr(step, "step"):
        step = step.step
    return [step] if isinstance(step, CommandStep) else []


def test_every_command_of_the_built_run_starts_due_parts_while_it_waits(monkeypatch):
    """A margin check or a slow weather step running past 14:38 never holds back the 3 pm parts."""
    from fno.config import load_app_config
    from fno.daily import wiring

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda cfg, root: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    runner = wiring.build_day_runner(load_app_config(), sleep=lambda seconds: None)
    commands = [c for step in seen["day_steps"].values() for c in _command_steps(step)]
    assert len(commands) >= 5  # margin check, weather, v4 forecasts, Book 1, card, candles
    due = []
    monkeypatch.setattr(runner.parts, "start_due", lambda: due.append(1))
    for command in commands:
        command.sleep(1.0)
    assert len(due) == len(commands)


def test_a_rerun_that_never_opens_the_day_starts_nothing_and_never_fails_on_a_wait():
    """A rerun whose log already holds `quotes` never calls `start` (judge 178 note 4); every wait still services the
    parts (found by O2's kill-and-rerun day: it raised on the first wait)."""
    clock = Clock()
    processes = FakeProcesses(clock, {})
    parts = QuoteParts(QUOTE_PARTS, processes, RecordingCommitter(clock, []), lambda specs: [], None, clock)
    parts.start_due()
    parts.service()
    assert processes.started == [] and not parts.busy()
