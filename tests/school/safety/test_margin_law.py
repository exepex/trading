"""Story section 6 item 7 (orchestrator, 22 Oct 2026): law 3's margin room runs C2's `MarginRoom` (failing closed)
only where every position of the check has a row in C2's margins file, which holds NIFTY's rows only; otherwise it
refuses with the note "margin not checked: no data" and no number (orchestrator, revised: design 6.1a). A missing or
malformed file refuses too, through C2."""

import pytest

from fno.risk.margins import MARGIN_COLUMNS
from fno.risk.rules import MarginRoom
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.school.constants import RefusalReason, RoadCode
from fno.school.safety.c2_laws import C2Law, margin_numbers
from fno.school.safety.margin_law import MARGIN_NOT_CHECKED, MarginRoomLaw, MarginRows, margin_not_checked
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c

from .law_builders import CFG, FixedMargin, held, view

NIFTY = RoadCode.NIFTY_MONTHLY
POOR = view(cash=1_000.0, equity=1_000.0)


def rows_file(tmp_path, *rows: str):
    path = tmp_path / "margins.csv"
    path.write_text(",".join(MARGIN_COLUMNS) + "\n" + "".join(r + "\n" for r in rows), encoding="utf-8")
    return MarginRows(path)


def law(rows: MarginRows) -> MarginRoomLaw:
    checked = C2Law("margin_room", MarginRoom(FixedMargin(), SimulatorTradeCosts(CFG["charges"])),
                    RefusalReason.MARGIN_ROOM, margin_numbers, {})  # fmt: skip
    return MarginRoomLaw(checked, rows)


PCS_100 = "PCS,100,1,1,1,NSE SPAN fixture,2026-11-01"


def nifty(snapshot=None):
    return snapshot or b.snapshot(NIFTY)


def test_a_nifty_position_with_a_row_is_checked_and_fails_closed(tmp_path):
    margin = law(rows_file(tmp_path, PCS_100))
    passed = margin.check(b.put_spread(), view(), nifty(), b.SESSION)
    assert passed.passed and passed.value is not None and not margin_not_checked(passed) and passed.note == ""
    assert margin.check(b.put_spread(), POOR, nifty(), b.SESSION).reason == RefusalReason.MARGIN_ROOM
    c.check_safety_law(margin, (b.put_spread(), view()), (b.put_spread(), POOR), nifty())


@pytest.mark.parametrize(
    ("rows", "road", "why"),
    [
        ((PCS_100,), RoadCode.BANKNIFTY_MONTHLY, "NIFTY's rows never price another index"),
        (("PCS,200,1,1,1,NSE SPAN fixture,2026-11-01",), NIFTY, "no row for this width"),
        (("SC,100,1,1,1,NSE SPAN fixture,2026-11-01",), NIFTY, "no row for this structure"),
        (("PCS,100,1,1,1,,2026-11-01",), NIFTY, "an unsourced row is no data"),
    ],
)
def test_no_row_refuses_noted_never_a_number(tmp_path, rows, road, why):
    result = law(rows_file(tmp_path, *rows)).check(b.put_spread(), view(), b.snapshot(road), b.SESSION)
    assert not result.passed and result.reason == RefusalReason.MARGIN_ROOM, why
    assert margin_not_checked(result) and (result.limit, result.value) == (None, None), why
    assert MARGIN_NOT_CHECKED == "margin not checked: no data"


def test_a_held_position_without_a_row_refuses_the_account_s_entries(tmp_path):
    other = held("h1", road=RoadCode.BANKNIFTY_MONTHLY)
    result = law(rows_file(tmp_path, PCS_100)).check(b.put_spread(), view(open_positions=(other,)), nifty(), b.SESSION)
    assert not result.passed and margin_not_checked(result)


@pytest.mark.parametrize("broken", ["missing", "layout"])
def test_a_missing_or_malformed_file_is_refused_not_unchecked(tmp_path, broken):
    path = tmp_path / "margins.csv"
    if broken == "layout":
        path.write_text("structure,width\nPCS,100\n", encoding="utf-8")
    real = MarginRoomLaw(C2Law("margin_room", MarginRoom(_Unreadable(), SimulatorTradeCosts(CFG["charges"])),
                               RefusalReason.MARGIN_ROOM, margin_numbers, {}), MarginRows(path))  # fmt: skip
    refused = real.check(b.put_spread(), view(), b.snapshot(), b.SESSION)
    assert refused.reason == RefusalReason.MARGIN_ROOM and not margin_not_checked(refused), "C2's own refusal"


class _Unreadable(FixedMargin):
    def margin(self, terms, day):
        from fno.risk.inputs import RiskInputError

        raise RiskInputError("margin file missing")
