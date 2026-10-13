"""Story P6 (judge 42): past prices are put on today's share basis from NSE's corporate-actions list before 1W-1Y
changes, 52-week high and low, volume average and RSI are computed. KOTAKBANK's 5:1 split is the named case."""

import json
from datetime import date, timedelta

import pytest

from fno.fo_bhavcopy import BadFile
from fno.market_read_models.corporate_actions import adjusted, classify, read_corporate_actions
from fno.market_read_models.nse_files import EquityBar
from fno.market_read_models.session_rows import on_todays_basis
from fno.market_read_models.stock_rows import pct, stock_row

KOTAK_SPLIT = "Face Value Split (Sub-Division) - From Rs 5/- Per Share To Re 1/- Per Share"  # NSE's own text


def nse_list(*records) -> bytes:
    return json.dumps([{"symbol": s, "exDate": d, "subject": t, "series": "EQ"} for s, d, t in records]).encode()


def kotak_bars() -> list[EquityBar]:
    """251 sessions: 2,152.10 a year back (13 Oct 2025, judge 42), 2,132.60 the day before the split, 421.00 on the
    ex-date 14 Jan 2026, 443.40 on 12 Oct 2026 (NSE's closes)."""
    days = [date(2025, 10, 13) + timedelta(days=i) for i in range(251)]
    closes = [2152.10] + [2132.60] * 92 + [421.00] * 157 + [443.40]
    ex_date = days[93]
    return [EquityBar(d, "KOTAKBANK", "EQ", c, c * 1.01, c * 0.99, 1000 if d < ex_date else 5000)
            for d, c in zip(days, closes)], ex_date  # fmt: skip


def test_kotakbank_after_its_5_for_1_split_from_nses_corporate_actions_list():
    bars, ex_date = kotak_bars()
    actions = read_corporate_actions(nse_list(("KOTAKBANK", f"{ex_date:%d-%b-%Y}", KOTAK_SPLIT)), "list.json")
    assert [(a.ex_date, a.factor, a.breaks_history) for a in actions] == [(ex_date, 5.0, False)]
    row = stock_row(adjusted(bars, actions), "Kotak Mahindra Bank Limited", "Financial Services", None, [])
    assert row["y1"] == pct(443.40, 430.42) == 3.02  # unadjusted: -79.4%
    rebased = adjusted(bars, actions)
    assert rebased[1].high == round(2132.60 * 1.01 / 5, 2) and rebased[1].volume == 5000  # on the new share basis
    assert row["h"] == pytest.approx(443.40 * 1.01) and row["va"] == 5000.0  # unadjusted high: 2,173.62
    unadjusted = stock_row(bars, "Kotak", "", None, [])
    assert unadjusted["y1"] == pct(443.40, 2152.10) and unadjusted["y1"] < -79


@pytest.mark.parametrize(
    "subject, factor, breaks",
    [
        (KOTAK_SPLIT, 5.0, False),
        ("Face Value Split (Sub-Division) - From Rs 10/- Per Share To Rs 2/- Per Share", 5.0, False),
        ("Bonus 1:1", 2.0, False),
        ("Bonus 7:5", 2.4, False),
        ("Demerger", None, True),
        ("Scheme of Arrangement", None, True),
        ("Interim Dividend - Rs 2.50 Per Share", None, False),
        ("Buy Back", None, False),
    ],
)
def test_each_kind_of_action_in_nses_list(subject, factor, breaks):
    assert classify(subject) == (factor, breaks)


def test_a_demerger_uses_only_the_sessions_from_its_ex_date():
    bars, ex_date = kotak_bars()
    actions = read_corporate_actions(nse_list(("KOTAKBANK", f"{ex_date:%d-%b-%Y}", "Demerger")), "list.json")
    kept = adjusted(bars, actions)
    assert kept[0].day == ex_date and stock_row(kept, "K", "", None, [])["y1"] is None  # no ratio: no 1Y figure


def test_an_action_after_the_session_is_never_applied():
    bars, ex_date = kotak_bars()
    later = read_corporate_actions(nse_list(("KOTAKBANK", "15-Oct-2026", KOTAK_SPLIT)), "list.json")
    assert on_todays_basis({"KOTAKBANK": bars}, later, date(2026, 10, 12)) == {"KOTAKBANK": bars}


def test_a_list_that_is_not_nses_is_refused():
    with pytest.raises(BadFile):
        read_corporate_actions(b'{"not": "a list"}', "list.json")
