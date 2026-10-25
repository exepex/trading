"""REC1b's day conditions: problem steps without the school, the quote gate, and M1's weather, where a missing, not
live or unscored record is an input failure (owner, 15 Oct, "4 A"), never a pass."""

import json
from datetime import datetime

import pytest

from fno.desk.run_log import RunLog
from fno.recommend.conditions import RunLogConditions
from fno.recommend.ports import InputFailed
from fno.weather.records import WeatherRecords
from tests.recommend.builders import DAY

OK = {"status": "ok", "reason": "command:ok"}


def setup(root, steps: dict, weather: dict | None = None) -> RunLogConditions:
    log, now = RunLog.open(root, DAY), datetime.now().astimezone()
    for name, result in steps.items():
        log.record(name, now, now, {}, result)
    records = WeatherRecords(root / "weather")
    if weather is not None:
        records.path(DAY).parent.mkdir(parents=True, exist_ok=True)
        records.path(DAY).write_text(json.dumps(weather))
    return RunLogConditions(root, records)


def weather(colour: str = "GREEN", label: str = "live", status: str = "scored") -> dict:
    return {"day": DAY.isoformat(), "label": label, "status": status, "colour": colour}


def test_a_clean_day(tmp_path):
    found = setup(tmp_path, {"quotes_done": OK, "card": OK}, weather()).conditions(DAY)
    assert (found.step_problems, found.quote_gate_failed, found.weather_red) == (False, False, False)
    assert [ref.path for ref in found.used] == [f"journal/runs/{DAY}.json", f"weather/2026/{DAY}.json"]


def test_a_failed_or_refused_step_is_a_problem(tmp_path):
    steps = {"quotes_done": OK, "fills": {"status": "refused", "reason": "desk:TOO_LATE"}}
    assert setup(tmp_path, steps, weather()).conditions(DAY).step_problems


def test_the_school_s_own_failure_is_its_source_s_state_not_a_step_problem(tmp_path):
    steps = {"quotes_done": OK, "school": {"status": "refused", "reason": "school:TOO_LATE"}}
    assert not setup(tmp_path, steps, weather()).conditions(DAY).step_problems


def test_a_failed_quote_capture_fails_the_gate(tmp_path):
    steps = {"quotes_done": {"status": "failed", "reason": "not ok: nifty"}}
    found = setup(tmp_path, steps, weather()).conditions(DAY)
    assert found.quote_gate_failed and found.step_problems


def test_a_red_day(tmp_path):
    assert setup(tmp_path, {"quotes_done": OK}, weather("RED")).conditions(DAY).weather_red


@pytest.mark.parametrize("record", [None, weather(label="backfill_exploratory"), weather(status="not scored"),
                                    weather(colour="PURPLE")])  # fmt: skip
def test_weather_that_is_missing_not_live_or_unscored_is_an_input_failure(tmp_path, record):
    with pytest.raises(InputFailed, match="weather record"):
        setup(tmp_path, {"quotes_done": OK}, record).conditions(DAY)


def test_no_run_log_or_no_quotes_done_is_an_input_failure(tmp_path):
    with pytest.raises(InputFailed, match="run log"):
        setup(tmp_path, {}, weather()).conditions(DAY)
    with pytest.raises(InputFailed, match="quotes_done"):
        setup(tmp_path, {"card": OK}, weather()).conditions(DAY)


def test_a_weather_or_log_file_that_does_not_read_is_an_input_failure(tmp_path):
    conditions = setup(tmp_path, {"quotes_done": OK}, weather())
    conditions.weather.path(DAY).write_text("{broken")
    with pytest.raises(InputFailed, match="does not read"):
        conditions.conditions(DAY)
