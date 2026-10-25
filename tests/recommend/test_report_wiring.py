"""REC1d's wiring: the evening's no-record line reads the run log's `recommend` status and reason code only (judge
664 m1; criterion h), and the switch is the recommender's own `daily.live_from.recommend`."""

from datetime import UTC, datetime

from fno.desk.run_log import RunLog
from fno.recommend.report_wiring import live_from, recommend_step
from tests.recommend.builders import DAY

AT = datetime(2026, 11, 2, 9, 55, tzinfo=UTC)


def logged(tmp_path, result):
    RunLog.open(tmp_path, DAY).record("recommend", AT, AT, {}, result)


def test_the_step_gives_its_status_and_code_never_its_printed_lines(tmp_path):
    logged(tmp_path, {"status": "failed", "reason": "recommend:NOT_POSTED", "lines": ["the 51200 put"]})
    assert recommend_step(tmp_path, DAY) == ("failed", "recommend:NOT_POSTED")


def test_a_free_text_reason_is_never_shown(tmp_path):
    logged(tmp_path, {"status": "failed", "reason": "the 51200 put could not be priced"})
    assert recommend_step(tmp_path, DAY) == ("failed", "unknown")


def test_no_step_logged_gives_none(tmp_path):
    assert recommend_step(tmp_path, DAY) is None


def test_the_switch_is_the_recommender_s_own_key_only():
    assert live_from({"school": {"reports": True}}) is None
    assert live_from({"daily": {"live_from": {"recommend": "2026-10-26"}}}).isoformat() == "2026-10-26"
    assert live_from({"daily": {"live_from": {"recommend": None}}}) is None
