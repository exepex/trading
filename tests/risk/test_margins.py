"""Story C2: margins are inputs with source and date; a missing, old or unset margin fails closed."""

from datetime import timedelta

import pytest

from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margins import MarginTable, MultiplierMargin, ScenarioLookupMargin
from fno.risk.settings import StressedMarginSettings

from .builders import DAY, FLY

TERMS = TradeTerms(FLY, 200, 2)
HEADER = "structure,width,margin_per_lot_rs,source,as_of\n"


def _table(tmp_path, rows: str, max_age: int = 7) -> MarginTable:
    path = tmp_path / "margins.csv"
    path.write_text(HEADER + rows)
    return MarginTable(path, max_age)


def _multiplier(table, factor=1.5, source="broker calculator, stressed case", as_of=DAY, max_age=30):
    return MultiplierMargin(table, StressedMarginSettings("multiplier", factor, source, as_of, max_age, None))


def test_margin_is_the_latest_row_on_or_before_the_day_times_lots(tmp_path):
    table = _table(
        tmp_path, "SF,200,40000,calc,2026-10-08\nSF,200,42000,calc,2026-10-12\nSF,200,99000,calc,2026-10-14\n"
    )
    assert table.margin(TERMS, DAY) == 84_000.0  # the 14 Oct row is in the future: never used


@pytest.mark.parametrize(("as_of", "ok"), [(DAY - timedelta(days=7), True), (DAY - timedelta(days=8), False)])
def test_a_margin_older_than_7_days_fails_closed(tmp_path, as_of, ok):
    table = _table(tmp_path, f"SF,200,40000,calc,{as_of}\n")
    if ok:
        assert table.margin(TERMS, DAY) == 80_000.0
    else:
        with pytest.raises(RiskInputError, match="older than 7 days"):
            table.margin(TERMS, DAY)


@pytest.mark.parametrize(
    "rows",
    [
        "",
        "SC,200,40000,calc,2026-10-12\n",
        "SF,150,40000,calc,2026-10-12\n",
        "SF,200,40000,,2026-10-12\n",
        "SF,200,0,calc,2026-10-12\n",
    ],
)
def test_a_missing_unsourced_or_zero_margin_fails_closed(tmp_path, rows):
    with pytest.raises(RiskInputError):
        _table(tmp_path, rows).margin(TERMS, DAY)


def test_a_missing_margin_file_fails_closed(tmp_path):
    with pytest.raises(RiskInputError, match="missing"):
        MarginTable(tmp_path / "none.csv", 7).margin(TERMS, DAY)


def test_multiplier_margin_and_its_record(tmp_path):
    stressed = _multiplier(_table(tmp_path, "SF,200,40000,calc,2026-10-12\n"))
    assert stressed.margin(TERMS, DAY) == 120_000.0
    record = stressed.record()
    assert record["method"] == "multiplier" and record["multiplier"] == "1.5" and record["as_of"] == "2026-10-13"
    assert record["source"] == "broker calculator, stressed case"


@pytest.mark.parametrize(
    ("factor", "source", "as_of"),
    [
        (None, "s", DAY),
        (1.5, None, DAY),
        (1.5, "s", None),
        (1.5, "s", DAY - timedelta(days=31)),
        (1.5, "s", DAY + timedelta(days=1)),
    ],
)
def test_an_unset_expired_or_future_multiplier_fails_closed(tmp_path, factor, source, as_of):
    stressed = _multiplier(_table(tmp_path, "SF,200,40000,calc,2026-10-12\n"), factor, source, as_of)
    with pytest.raises(RiskInputError, match="multiplier"):
        stressed.margin(TERMS, DAY)


def test_a_multiplier_exactly_30_days_old_is_still_valid(tmp_path):
    stressed = _multiplier(_table(tmp_path, "SF,200,40000,calc,2026-10-12\n"), as_of=DAY - timedelta(days=30))
    assert stressed.margin(TERMS, DAY) == 120_000.0


def _lookup(tmp_path, rows: str) -> ScenarioLookupMargin:
    path = tmp_path / "stressed.csv"
    path.write_text("structure,width,scenario,margin_per_lot_rs,source,as_of\n" + rows)
    settings = StressedMarginSettings("scenario_lookup", None, None, None, 30, path)
    return ScenarioLookupMargin(settings, ["down", "up"], 7)


def test_scenario_lookup_takes_the_largest_scenario_margin(tmp_path):
    lookup = _lookup(tmp_path, "SF,200,down,70000,span,2026-10-12\nSF,200,up,65000,span,2026-10-12\n")
    assert lookup.margin(TERMS, DAY) == 140_000.0
    assert lookup.record() == {"method": "scenario_lookup", "scenario_file": "stressed.csv"}


def test_scenario_lookup_without_every_scenario_fails_closed(tmp_path):
    with pytest.raises(RiskInputError, match="up"):
        _lookup(tmp_path, "SF,200,down,70000,span,2026-10-12\n").margin(TERMS, DAY)
