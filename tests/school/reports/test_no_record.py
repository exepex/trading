"""Story MS-P1j4: a session with no sealed school record is said so in the 20:05 section, with the daily run's
school step as its committed run log holds it; a counts line is never empty; the 08:50 section says when no plan can
be made."""

import json
from dataclasses import replace
from datetime import timedelta

import pytest

from fno.constants import SCHOOL_STEP
from fno.school.constants import NO_LATENCY_LABEL, NSE_TERMS_LINE, ClosureReason
from fno.school.contracts.reports import Banner
from fno.school.contracts.roads import RoadDay, RoadStatus
from fno.school.fakes import FakeDashcam
from fno.school.fleet.report_inputs import SealedDayInputs
from fno.school.reports.evening import HowDidTodayGoSection
from fno.school.reports.today import NO_CANDIDATE, NO_PLAN, TodaySection
from tests.school.contracts.test_records import closed_record, trade_record
from tests.school.reports import fakes as f

TITLE = "School pilot, How did today go (Paper: no real money, no order)"


def evening(items=(), rows=(), step=None):
    return HowDidTodayGoSection(f.Day(tuple(items), tuple(rows), step=step)).render(f.SESSION)


@pytest.mark.parametrize(
    ("step", "why"),
    [
        (None, "the daily run recorded no school step"),
        (("refused", "school:TOO_LATE"), "the daily run's school step was refused (school:TOO_LATE)"),
        (("failed", "school:STOPPED"), "the daily run's school step was failed (school:STOPPED)"),
        (("ok", "school:OFF"), "the daily run's school step was ok (school:OFF)"),
    ],
    ids=["no step", "too late", "stopped", "switch off"],
)
def test_a_session_with_no_sealed_record_says_so_and_why_and_nothing_else(step, why):
    text = evening(step=step)
    assert text.title == TITLE and text.banner is Banner.RED
    assert text.lines == (
        "Banner: RED, do not trade real money today",
        f"No school record for {f.SESSION}: {why}.",
        NO_LATENCY_LABEL,
        NSE_TERMS_LINE,
    )


def test_a_no_record_day_shows_no_rupee_no_trade_and_no_count_line():
    shown = "\n".join(evening(step=("failed", "school:STOPPED")).lines)
    assert "Rs" not in shown and "Trades closed" not in shown and "Counts" not in shown and "Fleet total" not in shown


def test_outcomes_alone_without_a_sealed_decisions_file_are_no_record():
    """The decisions file is the record: an outcome with no decisions is never shown as a day of trades."""
    assert f"No school record for {f.SESSION}" in evening([f.net_record()]).lines[1]


@pytest.mark.parametrize("step", [None, ("ok", "command:ok")], ids=["no step (a manual run)", "step ok"])
def test_a_recorded_day_is_unchanged_when_its_step_is_ok_or_missing(step):
    """Criterion 5; that the render is as before is carried by g's tests in `test_sections.py`."""
    recorded = evening([trade_record(), f.net_record()], [f.counts()])
    assert recorded == evening([trade_record(), f.net_record()], [f.counts()], step=step)
    assert recorded.banner is Banner.AMBER and "may be incomplete" not in "\n".join(recorded.lines)


def test_a_day_that_sealed_and_then_stopped_says_so_in_red_never_a_quiet_amber_day():
    """Judge 645's case: one sealed trade decision, no outcome or counts (`_finish` stopped), the step failed."""
    text = evening([trade_record()], step=("failed", "school:STOPPED"))
    assert text.banner is Banner.RED
    assert text.lines[:2] == (
        "Banner: RED, do not trade real money today",
        "the daily run's school step was failed (school:STOPPED): this record may be incomplete",
    )


@pytest.mark.parametrize("step", [("refused", "school:TOO_LATE"), ("failed", "o1:STOPPED_AT_LIMIT")])
def test_any_step_that_is_not_ok_on_a_recorded_day_adds_its_line_and_the_red_banner(step):
    text = evening([trade_record(), f.net_record()], [f.counts()], step=step)
    line = f"the daily run's school step was {step[0]} ({step[1]}): this record may be incomplete"
    assert text.banner is Banner.RED and line in text.lines and "CS1@1 BANKNIFTY-M: 3 / 2 / 1" in text.lines


def test_a_recorded_day_with_no_counts_row_says_none_never_an_empty_line():
    lines = evening([closed_record()]).lines
    assert "Counts (eligible / fillable / executed): none" in lines
    assert "Counts (eligible / fillable / executed):" not in lines


def test_a_counts_row_of_a_control_only_still_says_none():
    assert "Counts (eligible / fillable / executed): none" in evening([closed_record()], [f.counts("N0@1")]).lines


def all_closed() -> tuple[RoadDay, ...]:
    return tuple(replace(d, status=RoadStatus(ClosureReason.CAPTURE_MISSING)) for d in f.open_roads())


@pytest.mark.parametrize("days", [all_closed(), ()], ids=["every road closed", "no road listed"])
def test_today_says_no_plan_can_be_made_when_no_road_is_open(days):
    lines = TodaySection(f.Today(days=days, trades=())).render(f.SESSION).lines
    body = [line for line in lines if line.startswith(("No plan", "No candidate"))]
    assert body == [f"{NO_PLAN} (plan from {f.SESSION - timedelta(days=1):%d %b %Y} 15:00 data, indicative "
                    "prices, not today's quotes)"]  # fmt: skip


def test_today_with_an_open_road_and_no_proposal_keeps_no_candidate():
    lines = "\n".join(TodaySection(f.Today(days=f.roads_with_one_closed(), trades=())).render(f.SESSION).lines)
    assert NO_CANDIDATE in lines and NO_PLAN not in lines


def test_today_with_a_plan_is_unchanged():
    lines = "\n".join(TodaySection(f.Today()).render(f.SESSION).lines)
    assert NO_PLAN not in lines and NO_CANDIDATE not in lines and "worst loss" in lines


def write_log(root, steps) -> None:
    folder = root / "journal" / "runs"
    folder.mkdir(parents=True)
    (folder / f"{f.SESSION}.json").write_text(json.dumps({"day": str(f.SESSION), "steps": steps}))


def reader(root) -> SealedDayInputs:
    return SealedDayInputs(FakeDashcam(), root, f.ROLES)


def test_the_reader_takes_the_school_step_s_status_and_code_from_the_committed_run_log(tmp_path):
    write_log(tmp_path, {SCHOOL_STEP: {"result": {"status": "refused", "reason": "school:TOO_LATE"}}})
    assert reader(tmp_path).school_step(f.SESSION) == ("refused", "school:TOO_LATE")


def test_the_reader_says_none_with_no_log_or_no_school_step(tmp_path):
    assert reader(tmp_path).school_step(f.SESSION) is None
    write_log(tmp_path, {"card": {"result": {"status": "ok", "reason": "command:ok"}}})
    assert reader(tmp_path).school_step(f.SESSION) is None


def test_a_run_log_that_cannot_be_read_raises_for_g_s_guard_to_alert(tmp_path):
    folder = tmp_path / "journal" / "runs"
    folder.mkdir(parents=True)
    (folder / f"{f.SESSION}.json").write_text("{not json")
    with pytest.raises(ValueError):
        reader(tmp_path).school_step(f.SESSION)


class BrokenLog(f.Day):
    """A run log that cannot be read (bad JSON, or a school step without its result)."""

    def __init__(self, error: Exception):
        super().__init__()
        self.error = error

    def school_step(self, session):
        raise self.error


@pytest.mark.parametrize("error", [ValueError("Expecting value"), KeyError("result")], ids=["bad json", "no result"])
def test_a_run_log_that_cannot_be_read_alerts_and_the_edition_posts_without_a_guess(error):
    """Criterion 2 end to end: g's maker turns the raise into one alert naming its class; no "no school step" line."""
    from fno.school.reports.guard import with_school_sections
    from tests.school.reports.test_editions import GOLDEN, ON, lab_maker, make

    made = make(with_school_sections(lab_maker("evening"), ON, f.Today(), BrokenLog(error)), "evening")
    assert made.text == (GOLDEN / "evening.txt").read_text() and "No school record" not in made.text
    assert made.alerts == (
        f"school evening section not made ({type(error).__name__}); the edition was posted without it",
    )
