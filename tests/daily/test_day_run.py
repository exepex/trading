"""Story O1, criteria 1-5 and 7: one day of the daily run over E3's real `DailyRun` with fake O1 steps and fake quote
parts: the step order is `DAILY_RUN_STEPS`, the parts run beside the desk and commit their own files (NIFTY first),
a failing O1 step never stops the next, and after E3's commit-failure stop the card does not run."""

from datetime import timedelta

import pytest

from fno.constants import BOOK1_RULES, DAILY_RUN_STEPS, DESK_RUN_STEPS, STEP_FAILED, STEP_OK, STEP_REFUSED
from fno.daily.quote_parts import GROWW_QUOTES, PART_NOT_OK, QUOTE_PARTS
from fno.daily.quote_steps import NOT_IN_THIS_RUN, FinishQuoteParts, StartQuoteParts
from fno.daily.runner import DAY_DONE, NO_CARD, DayRunner
from fno.daily.steps import Alerted
from fno.desk.daily_ports import CommitFailed
from fno.desk.pending_commit import PendingCommitter
from tests.desk.builders import at
from tests.timetable.fakes import C4, Commits, Decisions, Rules, daily_run
from tests.timetable.test_daily_run import HOLIDAY, NORMAL, decided

from .fakes import RecordedStep, RecordingCommitter, quote_parts

NIFTY, NSE, INDICES = (part.arguments for part in QUOTE_PARTS)
NIFTY_SPEC, NSE_SPEC, BANKNIFTY_SPEC = GROWW_QUOTES.format(name="nifty"), "research/data/quotes/nse/", (
    GROWW_QUOTES.format(name="banknifty"))  # fmt: skip
FILES = {NIFTY_SPEC: ["nifty.canonical"], NSE_SPEC: ["nse.canonical"], BANKNIFTY_SPEC: ["banknifty.canonical"]}


def script(nifty=(14, 56), nse=(14, 57), indices=(15, 13), day=NORMAL):
    return {NIFTY: (at(*nifty, day=day), 0, ["recorded: nifty (complete=True)"]),
            NSE: (at(*nse, day=day), 0, ["recorded: nse (complete=True)"]),
            INDICES: (at(*indices, day=day), 0, ["recorded: 3 indices"])}  # fmt: skip


class FailingDesk(Commits):
    def __init__(self, clock, step):
        super().__init__(clock)
        self.step = step

    def commit(self, paths, message, own_unpushed=None):
        if message.endswith(f"step {self.step}"):
            raise CommitFailed("pull failed: origin unreachable")
        return super().commit(paths, message, own_unpushed)


@pytest.fixture
def day(root, tmp_path, alerts):
    """A day's run: E3's desk with Book 1, the five O1 steps, the quote parts on a recording committer."""

    def build(times=None, steps=None, desk_fails="", part_fails="", files=FILES):
        decisions = Decisions()
        decisions.add(*decided(BOOK1_RULES, "t1", NORMAL), NORMAL)
        run, clock, _, commits = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
        if desk_fails:
            run.committer = PendingCommitter(FailingDesk(clock, desk_fails), root)
        commits_made = []
        parts, waiter = quote_parts(clock, times or script(), RecordingCommitter(clock, commits_made, part_fails),
                                    alerts, files)  # fmt: skip
        calls = []
        run.waiter, run.day_steps = (
            waiter,
            {
                "margin_check": RecordedStep("margin_check", calls),
                "weather": RecordedStep("weather", calls),
                "forecasts_v4": RecordedStep("forecasts_v4", calls),
                "quotes": StartQuoteParts(parts),
                "owner_timing_fills": RecordedStep("owner_timing_fills", calls),
                "book1": RecordedStep("book1", calls),
                "reviews": RecordedStep("reviews", calls),
                "quotes_done": FinishQuoteParts(parts, waiter),
                "card": RecordedStep("card", calls),
                "price_distribution": RecordedStep("price_distribution", calls),
                "candles": RecordedStep("candles", calls),
            }
            | (steps or {}),
        )
        clock.now = at(14, 35, day=NORMAL)
        return DayRunner(run, parts, waiter), run, clock, parts, commits_made, calls

    return build


def test_a_session_runs_every_step_once_in_the_tuple_s_order(day):
    runner, run, _, _, _, calls = day()
    code, line = runner.run(NORMAL)
    log = run.run(NORMAL)  # a rerun the same day repeats nothing (criterion 3)
    assert (code, line) == (0, DAY_DONE)
    assert tuple(log.steps) == DAILY_RUN_STEPS and calls == [
        "owner_timing_fills", "margin_check", "weather", "forecasts_v4", "book1", "reviews", "card",
        "price_distribution", "candles",
    ]  # fmt: skip


def test_the_desk_s_own_steps_are_exactly_its_tuple_in_order(root, tmp_path, alerts):
    """E3's tests run without O1's steps: what the desk writes is exactly DESK_RUN_STEPS, inside DAILY_RUN_STEPS."""
    decisions = Decisions()
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), decisions, C4(), Rules())
    clock.now = at(14, 50, day=NORMAL)
    assert tuple(run.run(NORMAL).steps) == DESK_RUN_STEPS


def test_a_closed_day_records_only_skipped_its_parts_say_so_and_nothing_is_committed(day):
    """The parts start before the run (so a Drive outage at the download never loses the NSE record); on a closed day
    each recorder's own calendar rule records nothing, and the runner waits for them to end."""
    runner, run, _, parts, commits, calls = day(files={})
    runner.run(HOLIDAY)
    assert list(run.run(HOLIDAY).steps) == ["skipped"] and calls == [] and commits == []
    assert not parts.busy() and set(parts.results) == {"nifty", "nse", "indices"}


def test_nifty_and_nse_start_together_the_indices_after_nifty_s_commit_nifty_commits_first(day):
    runner, run, _, parts, commits, _ = day(script(nifty=(14, 56), nse=(14, 55)))  # NSE ends first
    runner.run(NORMAL)
    started = {arguments: when for when, arguments in parts.processes.started}
    assert started[NIFTY] == started[NSE] == at(14, 38, day=NORMAL)  # A4's earliest start (EARLIEST_START), not 14:35
    assert started[INDICES] == at(14, 56, day=NORMAL)  # right after NIFTY's commit, not before
    assert [(when, message.split()[-1], paths) for when, message, paths in commits] == [
        (at(14, 56, day=NORMAL), "nifty", ("nifty.canonical",)),  # first, though NSE ended before it
        (at(14, 56, day=NORMAL), "nse", ("nse.canonical",)),
        (at(15, 13, day=NORMAL), "indices", ("banknifty.canonical",)),  # its own files only
    ]


def test_a_part_running_to_15_13_does_not_move_the_desk_s_steps(day):
    runner, run, *_ = day()
    runner.run(NORMAL)
    steps = run.run(NORMAL).steps
    assert steps["decisions"]["started_at"] == at(15, 12, day=NORMAL).isoformat()
    assert steps["snapshot"]["started_at"] == at(15, 15, day=NORMAL).isoformat()
    assert steps["quotes_done"]["result"]["status"] == STEP_OK


@pytest.mark.parametrize("name", ["margin_check", "weather", "forecasts_v4", "book1"])
@pytest.mark.parametrize("how", ["raises", "refused"])
def test_a_failing_o1_step_is_recorded_alerted_once_and_every_later_step_runs(day, alerts, name, how):
    calls = []
    refused = {"status": STEP_REFUSED, "reason": "nothing written: stale closes"}
    failing = (
        RecordedStep(name, calls, raises=RuntimeError("boom"))
        if how == "raises"
        else RecordedStep(name, calls, refused)
    )
    runner, run, *_ = day(steps={name: Alerted(name, failing, alerts)})
    code, line = runner.run(NORMAL)
    steps = run.run(NORMAL).steps
    status = STEP_FAILED if how == "raises" else STEP_REFUSED
    assert steps[name]["result"]["status"] == status and (code, line) == (1, f"day done with problems: {name}")
    assert [text for text in alerts.sent if f"step {name}" in text] == [alerts.sent[0]] and len(alerts.sent) == 1
    assert "exits" in steps and "card" in steps  # nothing later was skipped


@pytest.mark.parametrize("step", ["trade_marks", "reviews", "card"])
def test_a_stop_after_the_exits_never_says_the_exits_were_missed(day, alerts, step):
    code, line = day(desk_fails=step)[0].run(NORMAL)
    assert code == 1 and f"run STOPPED at step {step}" in line and "exits not reviewed today" not in line


def test_after_the_desk_s_commit_failure_stop_the_card_never_runs_and_the_parts_still_commit(day, alerts):
    runner, run, _, parts, commits, calls = day(desk_fails="pack")
    code, line = runner.run(NORMAL)
    assert code == 1 and line.endswith(NO_CARD) and "run STOPPED at step pack" in line
    assert "card" not in calls and len(alerts.sent) == 1  # E3's alert stands alone
    assert [message.split()[-1] for _, message, _ in commits] == ["nifty", "nse", "indices"]  # recorder's data kept


def test_a_part_commit_whose_push_failed_is_alerted_as_not_pushed_and_the_day_goes_on(day, alerts):
    """G4: the commit is made but its push was rejected: the run's one committer keeps it for the next push."""
    runner, run, *_ = day(part_fails="nse")
    code, line = runner.run(NORMAL)
    (sent,) = alerts.sent
    assert "quote part nse committed, NOT pushed (the next push carries it)" in sent
    assert (code, line) == (1, "day done with problems: quotes_done")
    assert "card" in run.run(NORMAL).steps


def test_a_rerun_skips_every_recorded_step_and_restarts_no_part(day, alerts):
    runner, run, clock, parts, commits, calls = day()
    run.day_steps["quotes_done"].run = lambda d: (_ for _ in ()).throw(KeyboardInterrupt())  # the routine is killed
    with pytest.raises(KeyboardInterrupt):
        runner.run(NORMAL)
    again, rerun, _, new_parts, _, new_calls = day()
    again.run(NORMAL)
    steps = rerun.run(NORMAL).steps
    assert calls == ["owner_timing_fills", "margin_check", "weather", "forecasts_v4", "book1", "reviews"]
    assert new_calls == ["card", "price_distribution", "candles"]
    assert not new_parts.started
    assert steps["quotes_done"]["result"] == {"status": STEP_FAILED, "reason": NOT_IN_THIS_RUN}


def test_a_hung_part_is_stopped_after_the_limit_and_the_ended_parts_are_committed(day):
    runner, run, clock, parts, commits, _ = day(script(nifty=(23, 0)))  # NIFTY never ends today
    runner.run(NORMAL)
    results = run.run(NORMAL).steps["quotes_done"]["result"]["parts"]
    assert parts.processes.made[NIFTY].stopped and results["nifty"]["status"] == STEP_FAILED
    assert results["indices"]["reason"].startswith("never started")
    assert [message.split()[-1] for _, message, _ in commits] == ["nse"]  # after the limit, NIFTY's files never
    assert clock() - at(15, 15, day=NORMAL) <= timedelta(minutes=21)


@pytest.mark.parametrize("name", ["quotes", "card"])
def test_quotes_or_card_raising_is_recorded_failed_with_one_alert(day, alerts, name):
    runner, run, *_ = day(steps={name: Alerted(name, RecordedStep(name, [], raises=OSError("disk full")), alerts)})
    code, line = runner.run(NORMAL)
    steps = run.run(NORMAL).steps
    assert steps[name]["result"] == {"status": STEP_FAILED, "reason": "OSError: disk full"}
    assert [text for text in alerts.sent] == [
        f"F&O daily run 2026-10-14: step {name} failed: OSError: disk full; the run goes on"
    ]
    assert "exits" in steps and code == 1  # the desk went on; with no part started, quotes_done says so (no alert)


@pytest.mark.parametrize("part", ["nifty", "nse", "indices"])
@pytest.mark.parametrize("own_alert", [True, False], ids=["alerted-itself", "silent"])
def test_a_failed_quote_part_is_alerted_once_by_itself_or_by_o1_and_the_others_still_commit(
    day, alerts, part, own_alert
):
    """A part that alerted for itself (its outcome line printed) gets no second alert (A4c); one that failed silently,
    as an incomplete Groww capture does, gets O1's one line (O2, owner 16 Oct: every failure alerts)."""
    times = script()
    arguments = next(p.arguments for p in QUOTE_PARTS if p.name == part)
    ends_at, _, _ = times[arguments]
    lines = ["stopped, nothing recorded", *(["alert sent to #fno-desk"] if own_alert else [])]
    times[arguments] = (ends_at, 1, lines)
    runner, run, _, parts, commits, _ = day(times)
    code, line = runner.run(NORMAL)
    results = run.run(NORMAL).steps["quotes_done"]["result"]
    assert (code, line) == (1, "day done with problems: quotes_done")
    assert alerts.sent == (
        [] if own_alert else [PART_NOT_OK.format(day=NORMAL, name=part, status="failed", reason=lines[-1])]
    )
    assert results["reason"] == f"not ok: {part}" and results["parts"][part]["reason"] == lines[-1]
    assert [message.split()[-1] for _, message, _ in commits] == ["nifty", "nse", "indices"]  # its files too


def test_a_failed_nifty_still_starts_the_indices_after_it_and_lets_nse_commit(day):
    times = script(nse=(14, 55))
    times[NIFTY] = (at(14, 58, day=NORMAL), 1, ["stopped, nothing recorded"])
    runner, run, _, parts, commits, _ = day(times)
    runner.run(NORMAL)
    started = {arguments: when for when, arguments in parts.processes.started}
    assert started[INDICES] == at(14, 58, day=NORMAL)  # after NIFTY ended, whatever its result
    assert [(when, message.split()[-1]) for when, message, _ in commits] == [
        (at(14, 58, day=NORMAL), "nifty"),
        (at(14, 58, day=NORMAL), "nse"),
        (at(15, 13, day=NORMAL), "indices"),
    ]


def test_a_drive_outage_at_the_download_never_loses_the_day_s_nse_record(day, alerts):
    """Judge D and the orchestrator (16 Oct): the parts start before E2c's download, so when Drive is down the run
    stops with E3's one alert, and the parts still end and commit their own files (NSE needs no Drive)."""
    from fno.desk.private_files import PrivateFilesUnavailable

    class DriveDown:
        def download(self):
            raise PrivateFilesUnavailable("Drive: 503 from the files API")

    runner, run, _, parts, commits, calls = day()
    run.files = DriveDown()
    code, line = runner.run(NORMAL)
    assert code == 1 and "run STOPPED at the download of the private paper records" in line and line.endswith(NO_CARD)
    assert [message.split()[-1] for _, message, _ in commits] == ["nifty", "nse", "indices"] and calls == []
    assert len(alerts.sent) == 1  # E3's stop alert stands alone


def _previous_session_log(root, reviews_result, exits=True):
    from fno.desk.run_log import RunLog

    log, at = RunLog.open(root, NORMAL), at_(15, 20)
    if exits:
        log.record("exits", at, at, {}, {})
    if reviews_result is not None:
        log.record("reviews", at, at, {}, reviews_result)


def at_(hour, minute):
    return at(hour, minute, day=NORMAL)


@pytest.mark.parametrize(("reviews", "exits", "blocked"), [
    ({"status": STEP_FAILED, "reason": "PlaybookError: bad file"}, True, True),
    ({"status": STEP_REFUSED, "reason": "no valid execution snapshot"}, True, True),
    (None, True, True),  # the exits ran but the reviews never did
    ({"status": STEP_OK, "reason": "2 scorecards"}, True, False),
    (None, False, False),  # a stop before the exits: `_unreviewed`'s rule, not this one
])  # fmt: skip
def test_unscored_last_session_blocks_new_entries_today_and_only_then(day, root, reviews, exits, blocked):
    """Judge 214: when the last session's scorecards and automatic pauses failed or did not run after its exits, a
    catastrophic loss may be unpaused, so no book opens anything new on the next session (its exits still run)."""
    from tests.timetable.test_daily_run import SLOW

    _, run, *_ = day()
    _previous_session_log(root, reviews, exits)
    unscored = run._unscored(SLOW)
    assert (BOOK1_RULES in unscored) is blocked
    assert not blocked or "did not run" in unscored[BOOK1_RULES]


def test_a_failed_review_step_blocks_the_next_session_s_entries_end_to_end(day, alerts):
    """Day 1's reviews raise (recorded failed, one alert); day 2's fills open nothing new for Book 1, its exits run."""
    from tests.timetable.test_daily_run import SLOW

    failing = Alerted("reviews", RecordedStep("reviews", [], raises=RuntimeError("playbook unreadable")), alerts)
    runner, run, clock, *_ = day(steps={"reviews": failing})
    runner.run(NORMAL)
    run.steps.decisions.add(*decided(BOOK1_RULES, "t9", SLOW), SLOW)
    clock.now = at(14, 35, day=SLOW)
    runner.run(SLOW)
    fills = run.run(SLOW).steps["fills"]["result"]
    assert fills[BOOK1_RULES]["outcome"] == "not filled" and "did not run" in fills[BOOK1_RULES]["reason"]
    assert "exits" in run.run(SLOW).steps
