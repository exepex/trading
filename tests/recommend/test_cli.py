"""REC1b criterion 14 (judge 654 S2; J's plant: removing `cmd_decide`'s session check): a day that is not an NSE trading
session (a weekend, a holiday, a muhurat-only day) records and posts nothing, and builds nothing that could."""

from datetime import date
from types import SimpleNamespace

import pytest

from fno.recommend import wiring
from fno.recommend.cli import NOT_A_SESSION, cmd_decide

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
