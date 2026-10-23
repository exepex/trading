"""Story C2: margins are inputs with source and date; a missing, old or unset margin fails closed."""

from datetime import timedelta

import pytest

from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MarginTable, MultiplierMargin, ScenarioLookupMargin
from fno.risk.settings import StressedMarginSettings
from fno.storage.table_source import FileTable
from tests.stress_factor_files import factor_file

from .builders import DAY, FLY

TERMS = TradeTerms(FLY, 200, 2)
HEADER = "structure,width,scan_per_lot_rs,nov_per_lot_rs,exposure_per_lot_rs,source,as_of\n"


def _table(tmp_path, rows: str, max_age: int = 7) -> MarginTable:
    path = tmp_path / "margins.csv"
    path.write_text(HEADER + rows)
    return MarginTable(FileTable(path), DaysOld(max_age), 65)


def _multiplier(table, factor=1.5, as_of=DAY - timedelta(days=1), max_age=30):
    """k from a factor file (story C2d): one row, dated the day before `DAY` by default."""
    return MultiplierMargin(table, StressedMarginSettings("multiplier", factor_file(factor, as_of), max_age, None))


def test_margin_is_the_latest_row_on_or_before_the_day_times_lots(tmp_path):
    table = _table(
        tmp_path,
        "SF,200,40000,0,0,calc,2026-10-08\nSF,200,42000,0,0,calc,2026-10-12\nSF,200,99000,0,0,calc,2026-10-14\n",
    )
    assert table.margin(TERMS, DAY) == 84_000.0  # the 14 Oct row is in the future: never used


@pytest.mark.parametrize(("as_of", "ok"), [(DAY - timedelta(days=7), True), (DAY - timedelta(days=8), False)])
def test_a_margin_older_than_7_days_fails_closed(tmp_path, as_of, ok):
    table = _table(tmp_path, f"SF,200,40000,0,0,calc,{as_of}\n")
    if ok:
        assert table.margin(TERMS, DAY) == 80_000.0
    else:
        with pytest.raises(RiskInputError, match="older than 7 days"):
            table.margin(TERMS, DAY)


@pytest.mark.parametrize(
    "rows",
    [
        "",
        "SC,200,40000,0,0,calc,2026-10-12\n",
        "SF,150,40000,0,0,calc,2026-10-12\n",
        "SF,200,40000,0,0,,2026-10-12\n",
        "SF,200,0,0,0,calc,2026-10-12\n",
    ],
)
def test_a_missing_unsourced_or_zero_margin_fails_closed(tmp_path, rows):
    with pytest.raises(RiskInputError):
        _table(tmp_path, rows).margin(TERMS, DAY)


def test_a_missing_margin_file_fails_closed(tmp_path):
    with pytest.raises(RiskInputError, match="missing"):
        MarginTable(FileTable(tmp_path / "none.csv"), DaysOld(7), 65).margin(TERMS, DAY)


def test_multiplier_margin_and_its_record(tmp_path):
    stressed = _multiplier(_table(tmp_path, "SF,200,40000,0,0,calc,2026-10-12\n"))
    assert stressed.margin(TERMS, DAY) == 120_000.0
    record = stressed.record(DAY)
    row = record["stress_factor_row"]
    assert record["method"] == "multiplier" and row["factor"] == "1.5" and row["as_of"] == "2026-10-12"
    assert row["status"] == "applied" and record["factor_file"].endswith(".csv")


@pytest.mark.parametrize(
    ("as_of", "said"),
    [
        (DAY - timedelta(days=31), "not valid on"),
        (DAY, "no factor row before"),
        (DAY + timedelta(days=1), "no factor row"),
    ],
)
def test_an_expired_same_day_or_future_factor_fails_closed(tmp_path, as_of, said):
    stressed = _multiplier(_table(tmp_path, "SF,200,40000,0,0,calc,2026-10-12\n"), as_of=as_of)
    with pytest.raises(RiskInputError, match=said):
        stressed.margin(TERMS, DAY)


def test_an_unset_factor_file_fails_closed(tmp_path):
    table = _table(tmp_path, "SF,200,40000,0,0,calc,2026-10-12\n")
    stressed = MultiplierMargin(table, StressedMarginSettings("multiplier", None, 30, None))
    with pytest.raises(RiskInputError, match="multiplier is not set"):
        stressed.margin(TERMS, DAY)


def test_a_multiplier_exactly_30_days_old_is_still_valid(tmp_path):
    stressed = _multiplier(_table(tmp_path, "SF,200,40000,0,0,calc,2026-10-12\n"), as_of=DAY - timedelta(days=30))
    assert stressed.margin(TERMS, DAY) == 120_000.0


def _lookup(tmp_path, rows: str) -> ScenarioLookupMargin:
    path = tmp_path / "stressed.csv"
    path.write_text("structure,width,scenario,margin_per_lot_rs,source,as_of\n" + rows)
    settings = StressedMarginSettings("scenario_lookup", None, 30, path)
    return ScenarioLookupMargin(settings, ["down", "up"], DaysOld(7))


def test_scenario_lookup_takes_the_largest_scenario_margin(tmp_path):
    lookup = _lookup(tmp_path, "SF,200,down,70000,span,2026-10-12\nSF,200,up,65000,span,2026-10-12\n")
    assert lookup.margin(TERMS, DAY) == 140_000.0
    assert lookup.record() == {"method": "scenario_lookup", "scenario_file": "stressed.csv"}


def test_scenario_lookup_without_every_scenario_fails_closed(tmp_path):
    with pytest.raises(RiskInputError, match="up"):
        _lookup(tmp_path, "SF,200,down,70000,span,2026-10-12\n").margin(TERMS, DAY)


def test_scenario_lookup_cannot_give_the_margin_at_entry_so_it_fails_closed(tmp_path):
    """A scenario row is one netted figure with no NOV: the funds at entry (judge 77 addendum 3) cannot be checked."""
    lookup = _lookup(tmp_path, "SF,200,down,70000,span,2026-10-12\nSF,200,up,65000,span,2026-10-12\n")
    with pytest.raises(RiskInputError, match="no NOV"):
        lookup.margin_at_entry(TERMS, DAY)


def test_the_margin_at_entry_stresses_the_scan_and_drops_the_premium_credit(tmp_path):
    """SF width 200 with scan 4,000, NOV -6,000 and exposure 50,000 a lot, factor 1.5, 2 lots: at entry
    max(0, 1.5 x 4,000 + 6,000) + 1.5 x 50,000 = 87,000 a lot (C2c: k stresses the exposure too; was 62,000); C2's
    netted margin is 6,000 less."""
    stressed = _multiplier(_table(tmp_path, "SF,200,4000,-6000,50000,calc,2026-10-12\n"))
    assert stressed.margin_at_entry(TERMS, DAY) == 174_000.0
    assert stressed.margin(TERMS, DAY) == 162_000.0
