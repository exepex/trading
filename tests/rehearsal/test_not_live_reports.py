"""REH1c (the orchestrator's ruling for the owner): in a rehearsal every report runs, even one not live in real runs,
and each of its posts says so in one more line; E8's owner-timing fills keep their real date; real runs unchanged."""

import os
from datetime import date

from fno.constants import ENV_FNO_REHEARSAL, ENV_FNO_REHEARSAL_NOT_LIVE, OWNER_TIMING_STEP
from fno.desk.daily_ports import DayStep
from fno.desk.daily_steps import StepOutcome
from fno.rehearsal.live_wiring import NOT_LIVE_UNSET, NotLiveInRealRuns, rehearsed_live, rehearsed_not_live
from fno.rehearsal.mode import Rehearsal, labelled

DAY = date(2026, 10, 23)
REAL = {"card": None, "weather": date(2026, 10, 22), "close_read": date(2026, 10, 26), OWNER_TIMING_STEP: None}


def env(tmp_path):
    return {ENV_FNO_REHEARSAL: Rehearsal.new(DAY, tmp_path, tmp_path).to_env()}


def test_a_report_not_live_on_the_day_runs_in_a_rehearsal_and_names_why(tmp_path):
    live, notes = rehearsed_live(REAL, env(tmp_path))
    assert live == {"card": DAY, "weather": date(2026, 10, 22), "close_read": DAY, OWNER_TIMING_STEP: None}
    assert notes == {"card": NOT_LIVE_UNSET, "close_read": "not live in real runs on 2026-10-23 (live from 2026-10-26)"}


def test_a_real_run_keeps_every_live_date_and_wraps_nothing():
    assert rehearsed_live(REAL, {}) == (REAL, {})
    steps = {"card": object()}
    assert rehearsed_not_live(steps, {}) == steps


class Posting(DayStep):
    def __init__(self):
        self.seen = None

    def run(self, day):
        self.seen = labelled("*DRY RUN*", "the card")
        return StepOutcome({}, {"status": "ok"})


def test_each_post_of_such_a_step_carries_the_line_and_only_while_it_runs():
    step = Posting()
    NotLiveInRealRuns(step, NOT_LIVE_UNSET).run(DAY)
    assert step.seen == f"*DRY RUN*\n{NOT_LIVE_UNSET}\nthe card"
    assert ENV_FNO_REHEARSAL_NOT_LIVE not in os.environ
    assert labelled("*DRY RUN*", "an alert") == "*DRY RUN*\nan alert"


def test_the_daily_run_wraps_every_step_not_live_on_the_replayed_day_with_its_note(monkeypatch, tmp_path):
    """Judge 564 F1: the daily run's composition root is what makes these steps run; dropping its one line must fail."""
    from fno.config import load_app_config
    from fno.daily import wiring
    from fno.daily.v4_wiring import step_notes

    monkeypatch.setenv(ENV_FNO_REHEARSAL, env(tmp_path)[ENV_FNO_REHEARSAL])
    monkeypatch.setenv("FNO_SLACK_BOT_TOKEN", "xoxb-test")
    cfg = load_app_config()
    _, notes = rehearsed_live(wiring.live_dates(cfg))
    steps = wiring.build_day_runner(cfg, sleep=lambda seconds: None).daily_run.day_steps
    wrapped = {name: step.note for name, step in steps.items() if isinstance(step, NotLiveInRealRuns)}
    expected = {name: note for name, note in step_notes(notes).items() if name in steps}  # G10: `v4_pack`'s two steps
    assert "card" in notes and wrapped == expected and {"v4_release", "v4_deadline"} <= set(wrapped)
