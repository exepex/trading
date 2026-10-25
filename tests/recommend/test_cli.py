"""REC1b criterion 14 (judge 654 S2; J's plant: removing `cmd_decide`'s session check): a day that is not an NSE trading
session (a weekend, a holiday, a muhurat-only day) records and posts nothing, and builds nothing that could."""

from datetime import date
from types import SimpleNamespace

import pytest

from fno.recommend import wiring
from fno.recommend.cli import NOT_A_SESSION, NOT_LIVE, cmd_decide

WEEKEND, HOLIDAY, MUHURAT, SESSION = date(2026, 10, 24), date(2026, 1, 26), date(2026, 11, 8), date(2026, 10, 23)


@pytest.mark.parametrize("day", [WEEKEND, HOLIDAY, MUHURAT])
def test_a_day_that_is_not_a_trading_session_records_nothing(monkeypatch, day):
    def nothing_may_be_built(*args, **kwargs):
        raise AssertionError("a closed day built the recommender")

    monkeypatch.setattr(wiring, "build_recommend_run", nothing_may_be_built)
    lines = []
    assert cmd_decide(SimpleNamespace(on=day), out=lines.append) == 0
    assert lines == [NOT_A_SESSION.format(day=day)]


def test_the_calendar_decides_with_the_trading_kinds_only():
    assert [wiring.is_session(d) for d in (WEEKEND, HOLIDAY, MUHURAT, SESSION)] == [False, False, False, True]


def test_a_session_day_builds_and_runs_the_day(monkeypatch):
    ran = []
    monkeypatch.setattr(wiring, "build_recommend_run", lambda cfg: SimpleNamespace(
        run=lambda day: ran.append(day) or SimpleNamespace(lines=("line",), ok=True)))  # fmt: skip
    assert cmd_decide(SimpleNamespace(on=SESSION), out=lambda line: None) == 0 and ran == [SESSION]


@pytest.fixture
def recommender_live(monkeypatch):
    """The check under a config where the recommender has a live date (the repository's own has none: STAB1)."""
    monkeypatch.setattr("fno.config.load_app_config", lambda: {"daily": {"live_from": {"recommend": "2026-10-26"}}})


def test_the_check_builds_nothing_and_succeeds_while_the_recommender_has_no_live_date(monkeypatch):
    """STAB1 (owner, 25 Oct 2026): the repository's config switches the recommender off; the evening routine's
    `recommend check` then prints one line and exits 0, without reading Drive, the dashcam or Slack."""
    from fno.recommend import check_wiring
    from fno.recommend.cli import cmd_check

    monkeypatch.setattr(check_wiring, "build_check_run", lambda: (_ for _ in ()).throw(AssertionError("built")))
    lines = []
    assert cmd_check(SimpleNamespace(on=SESSION), out=lines.append) == 0 and lines == [NOT_LIVE.format(day=SESSION)]


def test_the_check_command_prints_its_lines_and_fails_only_on_its_own_problem(monkeypatch, recommender_live):
    from fno.recommend import check_wiring
    from fno.recommend.cli import cmd_check

    for ok, code in ((True, 0), (False, 1)):
        monkeypatch.setattr(check_wiring, "build_check_run", lambda ok=ok: SimpleNamespace(
            run=lambda day: SimpleNamespace(lines=("checked",), ok=ok)))  # fmt: skip
        lines = []
        assert cmd_check(SimpleNamespace(on=SESSION), out=lines.append) == code and lines == ["checked"]


@pytest.mark.parametrize("day", [WEEKEND, HOLIDAY, MUHURAT])
def test_the_check_writes_nothing_on_a_day_that_is_not_a_trading_session(monkeypatch, recommender_live, day):
    """Self-review 6: criterion 14 for the check too."""
    from fno.recommend import check_wiring
    from fno.recommend.cli import cmd_check

    monkeypatch.setattr(check_wiring, "build_check_run", lambda: (_ for _ in ()).throw(AssertionError("built")))
    lines = []
    assert cmd_check(SimpleNamespace(on=day), out=lines.append) == 0 and lines == [NOT_A_SESSION.format(day=day)]
