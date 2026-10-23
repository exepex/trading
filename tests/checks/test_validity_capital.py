"""Story STR1b criteria 1 and 4 (C4 side): C4's own stressed margin per lot equals C2's on every one of NSE's real
14 Oct 2026 rows (all nine codes, every width), with the STR1 cap computed by C4's own code; and C4's margin-room record
names the margin row it used."""

import csv
from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.checks.validity_margin import stressed_per_lot
from fno.checks.validity_settings import MarginSettings
from fno.risk.inputs import TradeTerms
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MarginTable, MultiplierMargin
from fno.risk.settings import StressedMarginSettings
from fno.storage.table_source import FileTable
from tests.checks.test_validity_shapes import ONE_SIDE, ROWS
from tests.checks.validity_builders import SPOT, check, committed_store
from tests.checks.validity_proposal_builder import one_side_proposal
from tests.checks.validity_sources import Margins
from tests.stress_factor_files import factor_file

REAL_ROWS = Path(__file__).parents[1] / "risk" / "fixtures" / "margins_2026-10-14.csv"
DAY, LOT, K = date(2026, 10, 14), 65, 1.45
K_FILE = factor_file(K, DAY - timedelta(days=1))
C4 = MarginSettings(REAL_ROWS, 7, None, "multiplier", K_FILE, 30)
C2 = MultiplierMargin(
    MarginTable(FileTable(REAL_ROWS), DaysOld(7), LOT), StressedMarginSettings("multiplier", K_FILE, 30, None)
)
REAL = list(csv.DictReader(REAL_ROWS.open(encoding="utf-8")))


@pytest.mark.parametrize("key", [(r["structure"], float(r["width"])) for r in REAL], ids=str)
def test_c4_s_stressed_margin_equals_c2_s_on_every_real_row(key):
    code, width = key
    c4 = stressed_per_lot(REAL, (code, width, 1), DAY, C4, LOT)
    assert c4 == pytest.approx(C2.margin(TradeTerms(code, width, 1), DAY), abs=1e-6)


def test_c4_names_the_margin_row_it_used():
    spec, width = ONE_SIDE["CDS"]
    report = check(one_side_proposal("CDS", spec, width), store=committed_store(spot=SPOT), margins=Margins(ROWS))
    room = next(r for r in report.results if r.name == "margin_room")
    named = room.numbers["margin_row"]
    assert (named["structure"], float(named["width"]), named["source"]) == ("CDS", 200.0, "test fixture")
    assert {"as_of", "scan_per_lot_rs", "nov_per_lot_rs", "exposure_per_lot_rs"} <= set(named)


def test_an_appended_row_after_the_decision_changes_nothing():
    """A14 appends a later day's rows between the 15:00 decision and the fill: the decision day's row is still used."""
    spec, width = ONE_SIDE["CDS"]
    later = [dict(r, as_of="2026-10-15", exposure_per_lot_rs="1.0") for r in ROWS if r["structure"] == "CDS"]
    report = check(one_side_proposal("CDS", spec, width), store=committed_store(spot=SPOT),
                   margins=Margins(ROWS + later))  # fmt: skip
    room = next(r for r in report.results if r.name == "margin_room")
    assert report.ok and room.numbers["margin_row"]["as_of"] != "2026-10-15"
