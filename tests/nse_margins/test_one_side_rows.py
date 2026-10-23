"""Story STR1 criterion 8 (A14 side): margin rows for the one- and two-leg structures equal a hand calculation, LC
and LP also get a row at width 0 (ATM), and a structure the passed broker check did not cover is printed, never
written, without failing the job."""

from datetime import date

import pytest

from fno.composition import build_tradable_structures
from fno.config import load_app_config
from fno.constants import STRUCTURES_BOUGHT_ONLY
from fno.nse_margins.broker_approvals import Approval, BrokerApprovals
from fno.nse_margins.calculator import NseIndexOptionExposure, SpanMarginCalculator
from fno.nse_margins.job import NseMarginJob
from fno.nse_margins.rows import MarginRowBuilder
from fno.nse_margins.span_file import read_span_file
from fno.nse_margins.wiring import build_row_builder

from .span_builder import DAY, LOT, span_zip
from .test_job import MORNING, Alerts, done_before, margin_log, margins_file, weekday

ATM = dict.fromkeys(STRUCTURES_BOUGHT_ONLY, (0.0,))


def builder() -> MarginRowBuilder:
    calculator = SpanMarginCalculator(NseIndexOptionExposure(), LOT)
    return MarginRowBuilder(build_tradable_structures(), (100.0,), calculator, 30, ATM)


def rows():
    found = builder().rows(read_span_file(span_zip(), "nsccl.20261014.i1.zip"), "00", DAY)
    return {(r.structure, r.width): r.figure for r in found.rows}, found.skipped


# By hand from span_builder.SF_ARRAYS (a long position's loss per unit in scenarios 3 and 4) and SF_PRICES, spot
# 20,000, lot 65; exposure 2% x 20,000 x 65 = 26,000 per short leg (none for a bought option):
HAND = {
    ("CCS", 100.0): (max(100 - 70, -15 + 10) * LOT, -(120 - 35) * LOT, 26_000.0),
    ("CDS", 100.0): (max(-100 + 70, 15 - 10) * LOT, (120 - 35) * LOT, 26_000.0),
    ("PCS", 100.0): (max(-20 + 12, 90 - 55) * LOT, -(110 - 30) * LOT, 26_000.0),
    ("PDS", 100.0): (max(20 - 12, -90 + 55) * LOT, (110 - 30) * LOT, 26_000.0),
    ("LC", 0.0): (15 * LOT, 120 * LOT, 0.0),
    ("LP", 0.0): (20 * LOT, 110 * LOT, 0.0),
}


@pytest.mark.parametrize("key", sorted(HAND))
def test_each_new_codes_row_equals_the_hand_calculation(key):
    figure = rows()[0][key]
    assert (figure.span, figure.nov, figure.exposure) == pytest.approx(HAND[key])


def test_every_code_gets_a_row_and_lc_lp_also_at_width_0():
    found, skipped = rows()
    assert skipped == []
    assert sorted(found) == sorted(
        [(code, 100.0) for code in ("SF", "SC", "BF", "LC", "LP", "CDS", "CCS", "PDS", "PCS")]
        + [("LC", 0.0), ("LP", 0.0)]
    )


def test_the_apps_builder_has_every_tradable_structure_and_the_atm_width_for_bought_only_codes():
    app = build_row_builder(load_app_config())
    assert [s.code for s in app.structures] == [s.code for s in build_tradable_structures()]
    assert app.extra_widths == ATM


def test_rows_of_unapproved_codes_are_printed_not_written_and_the_job_does_not_fail(tmp_path):
    path, alerts, printed = margins_file(tmp_path, done_before(DAY)), Alerts(), []
    check = BrokerApprovals({c: Approval("test: broker check", date(2026, 10, 1)) for c in ("SF", "SC", "BF")})
    day_file = lambda day: (f"nsccl.{day:%Y%m%d}.i1.zip", {DAY: span_zip()}.get(day))  # noqa: E731
    job = NseMarginJob(day_file, builder(), margin_log(path), weekday, check, alerts, lambda: MORNING, printed.append)
    assert job.run() == 0 and alerts.sent == []
    written = [line.split(",")[0] for line in path.read_text().splitlines()[8:]]
    assert written == ["SF", "SC", "BF"]
    held = next(line for line in printed if "not written" in line)
    assert "8 rows" in held and "CCS, CDS, LC, LP, PCS, PDS" in held
    assert sum(line.split(",")[0] in ("LC", "LP", "CDS", "CCS", "PDS", "PCS") for line in printed) == 8
