"""Fire once, even across a crash (story F1t criterion 2): the `firing` log is committed before any trigger call, a
rerun never fires again, and a leftover `firing` entry becomes `fire_unknown`."""

import json
from datetime import datetime

import pytest

from fno.ai.fire_once import FIRE_UNKNOWN, FIRED, FIRING, NOT_FIRED, FireLogRefused, FireOnceLog
from fno.models import IST

NOW = datetime(2026, 10, 19, 15, 0, tzinfo=IST)
PATH = "journal/ai_decisions/2026/2026-10-19_fired.json"
PLAN = {"book2_hybrid": {"fire": True, "version": "v2"}, "book3_ai": {"version": "v3", "reason": "budget stop"}}


class Recorder:
    """Records each commit with the log as it was then, and each fire with the log as it was then."""

    def __init__(self, root):
        self.root, self.commits, self.fires = root, [], []

    def commit(self, paths, message):
        self.commits.append((message, json.loads((self.root / PATH).read_text())))

    def fire(self, name):
        self.fires.append((name, json.loads((self.root / PATH).read_text())))
        return {"fired": True, "session": f"https://example.invalid/{name}"}


def test_the_firing_log_is_committed_before_any_trigger_call_then_results_are_written(tmp_path):
    recorder = Recorder(tmp_path)
    log = FireOnceLog(tmp_path, PATH, recorder.commit, lambda: NOW).fire(PLAN, recorder.fire, "F1t fire")
    ((message, committed),) = recorder.commits
    assert "about to fire book2_hybrid" in message and committed["book2_hybrid"]["state"] == FIRING
    assert recorder.fires == [("book2_hybrid", committed)]  # fired only after that commit
    assert log["book2_hybrid"] == {
        "version": "v2",
        "state": FIRED,
        "fired": True,
        "fired_at": NOW.isoformat(),
        "session": "https://example.invalid/book2_hybrid",
    }
    assert log["book3_ai"] == {"version": "v3", "reason": "budget stop", "state": NOT_FIRED, "fired": False}
    assert json.loads((tmp_path / PATH).read_text()) == log


def test_a_rerun_never_fires_again(tmp_path):
    recorder = Recorder(tmp_path)
    fire_log = FireOnceLog(tmp_path, PATH, recorder.commit, lambda: NOW)
    first = fire_log.fire(PLAN, recorder.fire, "F1t fire")
    assert fire_log.fire(PLAN, recorder.fire, "F1t fire") == first
    assert len(recorder.fires) == 1 and len(recorder.commits) == 1


def test_a_crash_between_the_call_and_its_record_leaves_fire_unknown_on_the_rerun(tmp_path):
    recorder = Recorder(tmp_path)

    def dies(name):
        raise SystemExit("container lost")  # not an Exception: the process ends mid-fire

    with pytest.raises(SystemExit):
        FireOnceLog(tmp_path, PATH, recorder.commit, lambda: NOW).fire(PLAN, dies, "F1t fire")
    rerun = FireOnceLog(tmp_path, PATH, recorder.commit, lambda: NOW).fire(PLAN, recorder.fire, "F1t fire")
    assert recorder.fires == []
    assert rerun["book2_hybrid"]["state"] == FIRE_UNKNOWN and rerun["book2_hybrid"]["fired"] is None
    assert "not fired again" in rerun["book2_hybrid"]["reason"]


def test_a_trigger_that_raises_is_fire_unknown_never_not_fired(tmp_path):
    recorder = Recorder(tmp_path)

    def broken(name):
        raise RuntimeError("socket closed after send")

    log = FireOnceLog(tmp_path, PATH, recorder.commit, lambda: NOW).fire(PLAN, broken, "F1t fire")
    assert log["book2_hybrid"]["state"] == FIRE_UNKNOWN
    assert log["book2_hybrid"]["reason"] == "RuntimeError: socket closed after send"


def test_a_trigger_refusal_is_not_fired_with_its_reason(tmp_path):
    recorder = Recorder(tmp_path)
    log = FireOnceLog(tmp_path, PATH, recorder.commit, lambda: NOW).fire(
        PLAN, lambda name: {"fired": False, "reason": "HTTP 429"}, "F1t fire"
    )
    assert (log["book2_hybrid"]["state"], log["book2_hybrid"]["reason"]) == (NOT_FIRED, "HTTP 429")


def test_a_failed_first_commit_fires_nothing(tmp_path):
    def refuses(paths, message):
        raise RuntimeError("push rejected")

    fires = []
    with pytest.raises(RuntimeError, match="push rejected"):
        FireOnceLog(tmp_path, PATH, refuses, lambda: NOW).fire(PLAN, fires.append, "F1t fire")
    assert fires == []


def test_nothing_to_fire_still_commits_the_log_and_calls_nothing(tmp_path):
    recorder = Recorder(tmp_path)
    plan = {"book2_hybrid": {"version": "v2", "reason": "not live"}}
    log = FireOnceLog(tmp_path, PATH, recorder.commit, lambda: NOW).fire(plan, recorder.fire, "F1t fire")
    assert "about to fire none" in recorder.commits[0][0] and recorder.fires == []
    assert log["book2_hybrid"]["state"] == NOT_FIRED


def test_a_file_that_is_not_a_fire_log_is_refused(tmp_path):
    (tmp_path / PATH).parent.mkdir(parents=True)
    (tmp_path / PATH).write_text(json.dumps({"book2_hybrid": {"fired": True}}))
    with pytest.raises(FireLogRefused, match="every entry needs a state"):
        FireOnceLog(tmp_path, PATH, Recorder(tmp_path).commit, lambda: NOW).read()
