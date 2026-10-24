"""Story G6 freeze, criterion 4: after the freeze, a look with the freeze broken records nothing and names every
problem; the report's first line says whether the freeze holds; before the freeze nothing changes (exploratory)."""

import json
from datetime import datetime, timedelta, timezone

from fno.forecast_scoring.v4.cli import FREEZE_INTACT, _look, _report, freeze_line
from fno.forecast_scoring.v4.days import DayCounts
from fno.forecast_scoring.v4.records import EXPLORATORY, LookRecords, NoRegistrations
from fno.forecast_scoring.v4.scoring import V4Scoring
from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds
from fno.forecast_v4.terms import LOOK_STOP_REVIEW
from tests.forecast_scoring_v4.helpers import settled_slot_days
from tests.forecast_scoring_v4.test_records_and_report import OneForecaster, Outcomes

AT = datetime(2027, 4, 30, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
BROKEN = ["fno/forecast_v4/terms.py: changed since the freeze (a change is a new version, never an edit)",
          "fno/v4_pack/new.py: added after the freeze"]  # fmt: skip


def _frozen(tmp_path) -> LookRecords:
    (tmp_path / "FREEZE_v4.md").write_text("# Freeze\nFrozen on: 2026-10-25\n", encoding="utf-8")
    return LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")


def _run_look(tmp_path, records, broken):
    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    return _look(scoring, records, FrozenToolThresholds(tmp_path), settled_slot_days(), LOOK_STOP_REVIEW, AT,
                 broken=lambda: broken)  # fmt: skip


def test_a_broken_freeze_stops_the_look_and_names_every_problem(tmp_path, capsys):
    records = _frozen(tmp_path)
    assert _run_look(tmp_path, records, BROKEN) == 1
    out = capsys.readouterr().out
    assert out.startswith("look NOT run, nothing recorded: v4 freeze BROKEN") and all(p in out for p in BROKEN)
    assert not records.path(LOOK_STOP_REVIEW).exists()


def test_an_intact_freeze_lets_the_look_record(tmp_path):
    records = _frozen(tmp_path)
    assert _run_look(tmp_path, records, []) == 0 and records.path(LOOK_STOP_REVIEW).exists()


def test_before_the_freeze_the_look_stays_exploratory_whatever_the_check_says(tmp_path, capsys):
    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    assert _run_look(tmp_path, records, BROKEN) == 0
    assert capsys.readouterr().out.startswith(EXPLORATORY) and not records.path(LOOK_STOP_REVIEW).exists()


def test_the_report_says_first_whether_the_freeze_holds(tmp_path, capsys):
    scoring, days = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations()), DayCounts(0, 0, 0, 0)
    records = _frozen(tmp_path)
    assert _report(scoring, records, "2026-10-30", days, []) == 0
    assert capsys.readouterr().out.splitlines()[0] == FREEZE_INTACT
    _report(scoring, records, "2026-10-31", days, BROKEN)
    assert capsys.readouterr().out.splitlines()[0] == freeze_line(BROKEN)
    assert json.loads((tmp_path / "v4_scores" / "2026-10-31.json").read_text())["freeze_problems"] == BROKEN


def test_the_report_before_the_freeze_has_no_freeze_line(tmp_path, capsys):
    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    _report(scoring, records, "2026-10-24", DayCounts(0, 0, 0, 0), BROKEN)
    first = capsys.readouterr().out.splitlines()[0]
    assert first == EXPLORATORY and "freeze_problems" not in json.loads((tmp_path / "v4_scores" / "2026-10-24.json")
                                                                        .read_text())  # fmt: skip
