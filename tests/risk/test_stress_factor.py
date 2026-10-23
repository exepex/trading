"""Story C2d: C2 and C4 read the stress factor k from A14c's file, never from config. Point in time (the latest row
dated strictly before the decision day), fail closed by name, the 30/31-day boundary, a held row's old factor, the
repository's seed row, a single source, and no change to any figure at the switch. Every case runs in C2 and in C4's
own reader (story C4: written apart)."""

from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.checks.validity_factor import FactorProblem, factor_on
from fno.checks.validity_margin import stressed_per_lot
from fno.checks.validity_settings import MarginSettings
from fno.config import ROOT, load_app_config
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MarginTable, MultiplierMargin
from fno.risk.settings import RiskSettingsError, StressedMarginSettings, risk_settings
from fno.risk.stress_factor import factor_in_force
from fno.storage.table_source import FileTable
from tests.risk.test_whole_margin_stress import REAL, REAL_ROWS
from tests.stress_factor_files import HEADER

SEED = date(2026, 10, 14)
LATER = date(2026, 11, 8)  # a Sunday: A14c's weekly row


def _file(tmp_path: Path, rows: str, header: str = HEADER) -> Path:
    path = tmp_path / "stress_factor.csv"
    path.write_text(header + rows, encoding="utf-8")
    return path


TWO_ROWS = f"{SEED},1.45,,,applied,seed,,\n{LATER},1.5,1.5,1.5,applied,peak,2026-11-06,abc\n"


def c2(path: Path | None, day: date) -> float:
    if path is None:
        raise RiskInputError("no file")
    return factor_in_force(path, day, 30).factor


def c4(path: Path | None, day: date) -> float:
    return factor_on(path, day, 30)[1]


BOTH = pytest.mark.parametrize(("read", "error"), [(c2, RiskInputError), (c4, FactorProblem)], ids=["C2", "C4"])


@BOTH
@pytest.mark.parametrize(("day", "factor"), [(date(2026, 11, 6), 1.45), (LATER, 1.45), (date(2026, 11, 9), 1.5)])
def test_the_factor_in_force_is_the_latest_row_before_the_day(tmp_path, read, error, day, factor):
    """A row dated on the decision day itself (here 8 Nov) is never used: a replay never sees a same-day row."""
    assert read(_file(tmp_path, TWO_ROWS), day) == factor


@BOTH
@pytest.mark.parametrize(
    ("rows", "header", "day", "said"),
    [
        (None, HEADER, date(2026, 10, 20), "missing"),
        (f"{SEED},1.45,,,applied,seed,,\n", "as_of,factor,status\n", date(2026, 10, 20), "columns must be"),
        (f"{SEED},1.45,,,applied,seed,,\n", HEADER, SEED, "no factor row before"),
        (f"{SEED},0.9,,,applied,seed,,\n", HEADER, date(2026, 10, 20), "factor 0.9"),
        (f"{SEED},1.45,,,approved,seed,,\n", HEADER, date(2026, 10, 20), "status 'approved'"),
        (f"{SEED},1.45,,,applied,seed,,\n", HEADER, date(2026, 11, 14), "not valid on 2026-11-14"),
    ],
    ids=["no file", "wrong header", "no row before", "below 1", "unknown status", "day 31"],
)
def test_every_unusable_factor_refuses_by_name(tmp_path, read, error, rows, header, day, said):
    path = tmp_path / "none.csv" if rows is None else _file(tmp_path, rows, header)
    with pytest.raises(error, match=said):
        read(path, day)


@BOTH
def test_day_30_passes_and_day_31_refuses(tmp_path, read, error):
    path = _file(tmp_path, f"{SEED},1.45,,,applied,seed,,\n")
    assert read(path, SEED + timedelta(days=30)) == 1.45  # 13 Nov
    with pytest.raises(error, match="not valid"):
        read(path, SEED + timedelta(days=31))  # 14 Nov


@BOTH
def test_a_held_row_keeps_the_old_factor_in_force(tmp_path, read, error):
    rows = f"{SEED},1.45,,,applied,seed,,\n{LATER},1.45,1.3,1.29,held,peak,2026-11-06,abc\n"
    assert read(_file(tmp_path, rows), date(2026, 11, 9)) == 1.45


def test_the_repository_seed_row_is_read_by_c2_and_c4():
    """`research/data/margins/stress_factor.csv` starts with the owner's 1.45 of 14 Oct (`peak` quoted, it holds a
    comma; no measured value). The file is append-only and A14c's rows are dated on their run day, so the seed is the
    first row, and the one in force on 15 Oct, whatever rows follow it."""
    path = ROOT / load_app_config()["risk"]["stressed_margin"]["factor_file"]
    assert path.read_text(encoding="utf-8").startswith(
        HEADER + '2026-10-14,1.45,,,applied,"owner seed: response 77, decision 14 Oct",,\n'
    )
    row = factor_in_force(path, date(2026, 10, 15), 30)
    assert (row.factor, row.status, row.evidence_sha256) == (1.45, "applied", "")
    assert factor_on(path, date(2026, 10, 15), 30) == (SEED, 1.45)


@pytest.mark.parametrize("key", ["multiplier", "source", "as_of"])
def test_the_factor_in_config_is_refused_at_start_up(key):
    cfg = load_app_config(overrides={"risk": {"stressed_margin": {key: "1.45" if key != "as_of" else "2026-10-14"}}})
    with pytest.raises(RiskSettingsError, match=f"{key} not allowed"):
        risk_settings(cfg, ROOT)


def test_the_switch_changes_no_figure_on_the_real_rows():
    """The seed's 1.45 gives C2c's figures on NSE's real 14 Oct rows (a decision on 15 Oct), in C2 and in C4."""
    seed, day = ROOT / load_app_config()["risk"]["stressed_margin"]["factor_file"], date(2026, 10, 15)
    c2_margin = MultiplierMargin(
        MarginTable(FileTable(REAL_ROWS), DaysOld(7), 65), StressedMarginSettings("multiplier", seed, 30, None)
    )
    c4_settings = MarginSettings(REAL_ROWS, 7, None, "multiplier", seed, 30)
    expected = {("SF", 100.0): 86_854.01, ("SC", 300.0): 98_012.27, ("BF", 300.0): 85_661.75, ("CCS", 300.0): 52_260.42}
    for (code, width), figure in expected.items():
        assert round(c2_margin.margin(TradeTerms(code, width, 1), day), 2) == figure
        assert round(stressed_per_lot(REAL, (code, width, 1), day, c4_settings, 65), 2) == figure


@BOTH
def test_of_two_rows_with_the_same_date_the_later_one_wins(tmp_path, read, error):
    """Append-only: a second row for the same day is its correction (judge 188), wherever the rows sit in the file."""
    rows = f"{SEED},1.45,,,applied,seed,,\n{LATER},1.5,1.5,1.5,applied,first,2026-11-06,a\n"
    rows += f"{LATER},1.6,1.6,1.6,applied,correction,2026-11-06,b\n"
    assert read(_file(tmp_path, rows), date(2026, 11, 9)) == 1.6
    earlier_first = f"{LATER},1.5,1.5,1.5,applied,first,2026-11-06,a\n{SEED},1.45,,,applied,seed,,\n"
    earlier_first += f"{LATER},1.6,1.6,1.6,applied,correction,2026-11-06,b\n"
    assert read(_file(tmp_path, earlier_first), date(2026, 11, 9)) == 1.6


@BOTH
@pytest.mark.parametrize(
    "bad_row",
    [
        f"{SEED},,,,applied,seed,,",  # empty factor
        "not-a-date,1.45,,,applied,seed,,",
        "20261014,1.45,,,applied,seed,,",  # only YYYY-MM-DD is accepted
        "2026-10-14T23:00,1.45,,,applied,seed,,",
        f"{SEED},1.45",  # a short row
        f"{SEED},nan,,,applied,seed,,",
        f"{SEED},inf,,,applied,seed,,",
    ],
    ids=["empty factor", "bad date", "compact date", "date-time", "short row", "nan", "inf"],
)
def test_an_unreadable_or_non_finite_row_anywhere_refuses_the_file_by_name(tmp_path, read, error, bad_row):
    """A14c appends unattended: a bad row, even one dated after the day, refuses with the file and row named."""
    path = _file(tmp_path, f"{SEED},1.45,,,applied,seed,,\n{bad_row}\n")
    with pytest.raises(error, match="stress_factor.csv row 3"):
        read(path, date(2026, 10, 20))
