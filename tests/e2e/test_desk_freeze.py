"""Story O1-desk-freeze, acceptance 1-3 through the real wiring: with `desk.frozen: true` the session records every
desk step `frozen`, starts no `desk book1` child, writes nothing in the accounts or Drive's private files, and keeps
the 3 pm quote parts, the timetable and every other step exactly as on the no-failure twin."""

import json
from datetime import date

import pytest

from fno.config import load_app_config
from fno.constants import DAILY_RUN_STEPS, DESK_FROZEN_STEPS

from . import harness
from .harness import QUOTES, fixture_day

FROZEN = {"status": "frozen", "reason": "desk:FROZEN"}


def with_switch(monkeypatch, frozen: bool) -> None:
    """The owner's one line, as `config.yaml` would hold it (the package's own file is never written)."""
    cfg = load_app_config()
    cfg = cfg | {"desk": cfg["desk"] | {"frozen": frozen}}
    monkeypatch.setattr(harness, "load_app_config", lambda: cfg)


def quote_tree(day) -> dict[str, bytes]:
    folder = day.root / QUOTES
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def without_commits(value):
    """A result without its commit hashes: each names its parent, so a history without desk commits differs."""
    if isinstance(value, dict):
        return {key: without_commits(item) for key, item in value.items() if key != "commit"}
    return value


def private_files(day) -> dict[str, bytes]:
    return {path: data for path, data in day.drive.files.items() if path.startswith("paper")}


@pytest.fixture(scope="module")
def days(tmp_path_factory):
    """The no-failure twin and the same session frozen, once per test process."""
    with pytest.MonkeyPatch.context() as patch:
        twin = fixture_day(tmp_path_factory.mktemp("twin"), patch)
        assert twin.run() == (0, "day done")
        capture = twin.step("snapshot")["snapshot_id"]  # the desk's 15:15 capture: its own step, frozen
        twin_quotes = {path: data for path, data in quote_tree(twin).items() if capture not in path}
        with_switch(patch, True)
        frozen = fixture_day(tmp_path_factory.mktemp("frozen"), patch)
        before = private_files(frozen)
        assert frozen.run() == (0, "day done") and frozen.slack.sent == []  # a decision, not a failure: no alert
        assert private_files(frozen) == before  # no account, fill or private pack written
        started = [key for _, key in frozen.children.started]
        return twin.log()["steps"], twin_quotes, frozen.log()["steps"], quote_tree(frozen), started


def test_a_frozen_session_keeps_the_timetable_and_the_quotes_and_runs_no_desk_step(days):
    twin_log, twin_quotes, log, quotes, started = days
    assert list(log) == list(DAILY_RUN_STEPS)
    assert {name: log[name]["result"] for name in DESK_FROZEN_STEPS} == dict.fromkeys(DESK_FROZEN_STEPS, FROZEN)
    assert ("desk", "book1") not in started
    assert {name: log[name]["started_at"] for name in log} == {name: twin_log[name]["started_at"] for name in log}
    assert quotes == twin_quotes and quotes  # the same 3 pm records, byte for byte; no 15:15 capture


def test_every_step_outside_the_desk_has_the_twin_s_result(days):
    twin_log, _, log, *_ = days
    others = [name for name in DAILY_RUN_STEPS if name not in DESK_FROZEN_STEPS]
    assert {name: without_commits(log[name]["result"]) for name in others} == {
        name: without_commits(twin_log[name]["result"]) for name in others}  # fmt: skip


def test_the_session_after_a_frozen_one_runs_the_whole_desk_and_blocks_nothing(tmp_path, monkeypatch):
    """Acceptance 4 through the real wiring: frozen on 13 Oct, the owner's one line, the full desk on 14 Oct."""
    with_switch(monkeypatch, True)
    day = fixture_day(tmp_path, monkeypatch)
    day.move_to(date(2026, 10, 13))
    assert day.run() == (0, "day done") and day.step("exits") == FROZEN
    with_switch(monkeypatch, False)
    day.move_to(date(2026, 10, 14))
    assert day.run() == (0, "day done") and day.slack.sent == []
    assert not [name for name, step in day.log()["steps"].items() if step["result"].get("status") == "frozen"]
    assert "fills:BLOCKED" not in json.dumps(day.step("fills")) and day.step("exits")["book1_rules"]["reviewed"]
