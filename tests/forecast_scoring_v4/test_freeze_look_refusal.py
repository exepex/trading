"""Story G6 freeze, criterion 4: after the freeze, a look with the freeze broken records nothing and names every
problem; the report's first line says whether the freeze holds; before the freeze nothing changes (exploratory)."""

import json
from datetime import datetime, timedelta, timezone

from fno.forecast_scoring.v4.cli import _look, _report
from fno.forecast_scoring.v4.days import DayCounts
from fno.forecast_scoring.v4.freeze_check import FreezeCheck
from fno.forecast_scoring.v4.records import EXPLORATORY, LookRecords, NoRegistrations
from fno.forecast_scoring.v4.scoring import V4Scoring
from fno.forecast_scoring.v4.thresholds import FrozenToolThresholds
from fno.forecast_v4.terms import LOOK_STOP_REVIEW
from tests.forecast_scoring_v4.helpers import settled_slot_days
from tests.forecast_scoring_v4.test_records_and_report import OneForecaster, Outcomes

AT = datetime(2027, 4, 30, 16, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
TERMS = "fno/forecast_v4/terms.py: changed since the freeze (a change is a new version, never an edit)"
BROKEN = FreezeCheck(problems=(TERMS, "fno/v4_pack/new.py: added after the freeze"))
DRIFTED = FreezeCheck(drift=("recorded file changed since the freeze: fno/analytics.py (norm_cdf)",))
SHALLOW = FreezeCheck(not_checked="shallow clone: run git fetch --unshallow origin main, then check again")


def _frozen(tmp_path) -> LookRecords:
    (tmp_path / "FREEZE_v4.md").write_text("# Freeze\nFrozen on: 2026-10-25\n", encoding="utf-8")
    return LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")


def _run_look(tmp_path, records, found: FreezeCheck):
    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    return _look(scoring, records, FrozenToolThresholds(tmp_path), settled_slot_days(), LOOK_STOP_REVIEW, AT,
                 freeze=lambda: found)  # fmt: skip


def test_a_broken_freeze_stops_the_look_and_names_every_problem(tmp_path, capsys):
    records = _frozen(tmp_path)
    assert _run_look(tmp_path, records, BROKEN) == 1
    out = capsys.readouterr().out
    assert out.startswith("look NOT run, nothing recorded: v4 freeze BROKEN") and all(p in out for p in BROKEN.problems)
    assert not records.path(LOOK_STOP_REVIEW).exists()


def test_a_shallow_clone_stops_the_look(tmp_path, capsys):
    records = _frozen(tmp_path)
    assert _run_look(tmp_path, records, SHALLOW) == 1 and not records.path(LOOK_STOP_REVIEW).exists()
    assert capsys.readouterr().out.startswith("look NOT run, nothing recorded: v4 freeze NOT CHECKED: shallow clone")


def test_an_intact_freeze_lets_the_look_record_with_its_drift_lines(tmp_path, capsys):
    records = _frozen(tmp_path)
    assert _run_look(tmp_path, records, DRIFTED) == 0 and records.path(LOOK_STOP_REVIEW).exists()
    assert capsys.readouterr().out.splitlines()[:2] == DRIFTED.lines()
    assert json.loads(records.path(LOOK_STOP_REVIEW).read_text())["freeze"] == DRIFTED.lines()


def test_before_the_freeze_the_look_stays_exploratory_whatever_the_check_says(tmp_path, capsys):
    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    assert _run_look(tmp_path, records, BROKEN) == 0
    assert capsys.readouterr().out.startswith(EXPLORATORY) and not records.path(LOOK_STOP_REVIEW).exists()


def test_the_report_says_first_whether_the_freeze_holds(tmp_path, capsys):
    scoring, days = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations()), DayCounts(0, 0, 0, 0)
    records = _frozen(tmp_path)
    assert _report(scoring, records, "2026-10-30", days, freeze=FreezeCheck()) == 0
    assert capsys.readouterr().out.splitlines()[0] == "v4 freeze: intact"
    _report(scoring, records, "2026-10-31", days, freeze=BROKEN)
    assert capsys.readouterr().out.splitlines()[0] == BROKEN.lines()[0]
    assert json.loads((tmp_path / "v4_scores" / "2026-10-31.json").read_text())["freeze"] == BROKEN.lines()
    _report(scoring, records, "2026-11-01", days, freeze=SHALLOW)
    assert capsys.readouterr().out.splitlines()[0].startswith("v4 freeze NOT CHECKED: shallow clone")


def test_the_report_before_the_freeze_has_no_freeze_line(tmp_path, capsys):
    scoring = V4Scoring(OneForecaster(), Outcomes(), NoRegistrations())
    records = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    _report(scoring, records, "2026-10-24", DayCounts(0, 0, 0, 0), freeze=BROKEN)
    first = capsys.readouterr().out.splitlines()[0]
    assert first == EXPLORATORY and "freeze" not in json.loads((tmp_path / "v4_scores" / "2026-10-24.json")
                                                                        .read_text())  # fmt: skip
