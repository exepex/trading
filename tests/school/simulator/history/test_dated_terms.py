"""Dated lots and dated STT (MS-SIM-a, 7.1 item 3)."""

from datetime import date
from pathlib import Path

import pytest
import yaml

from fno.school.simulator.history import edge1
from fno.school.simulator.history.ports import DayChain
from fno.school.simulator.terms import CIRCULAR_LOT, FILE_LOT, DatedTerms

CHARGES = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))["charges"]
TERMS = DatedTerms(edge1.circular_lot_or_none, edge1.dated_charges(CHARGES))


def chain(underlying="NIFTY", session=date(2021, 6, 1), lots=None):
    return DayChain(session, underlying, 15000.0, (), lots or {}, "legacy")


@pytest.mark.parametrize(
    ("underlying", "expiry", "lot"),
    [("NIFTY", date(2021, 6, 30), 75), ("NIFTY", date(2021, 7, 1), 50),  # NSE/FAOP/47854: from the July 2021 expiry
     ("BANKNIFTY", date(2020, 6, 25), 20), ("BANKNIFTY", date(2020, 7, 1), 25),
     ("BANKNIFTY", date(2023, 6, 29), 25), ("BANKNIFTY", date(2023, 7, 1), 15)],
)  # fmt: skip
def test_the_circular_lot_changes_on_both_sides_of_each_change(underlying, expiry, lot):
    found = TERMS.lot(chain(underlying), expiry)
    assert found.units == lot and CIRCULAR_LOT in found.source


def test_the_files_own_board_lot_wins_over_the_schedule():
    found = TERMS.lot(chain(lots={date(2021, 6, 30): 99}), date(2021, 6, 30))
    assert found.units == 99 and FILE_LOT in found.source


def test_an_index_with_no_schedule_and_no_file_lot_has_no_lot():
    assert TERMS.lot(chain("FINNIFTY"), date(2022, 1, 27)) is None  # closed, never guessed


def test_stt_is_the_rate_of_the_trade_date_on_both_sides_of_each_change():
    assert TERMS.charges(date(2023, 3, 31))["stt_sell_pct"] == 0.05
    assert TERMS.charges(date(2023, 4, 1))["stt_sell_pct"] == 0.0625
    assert TERMS.charges(date(2024, 9, 30))["stt_sell_pct"] == 0.0625
    assert TERMS.charges(date(2024, 10, 1))["stt_sell_pct"] == 0.1
    assert TERMS.charges(date(2026, 4, 1))["stt_sell_pct"] == 0.15


def test_only_the_stt_rates_change_and_the_decided_charges_stay():
    on = TERMS.charges(date(2022, 1, 3))
    assert {k: v for k, v in on.items() if not k.startswith("stt")} == {
        k: v for k, v in CHARGES.items() if not k.startswith("stt")
    }
