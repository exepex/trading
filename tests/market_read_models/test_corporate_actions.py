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
    assert [(a.ex_date, a.kind, a.factor) for a in actions] == [(ex_date, "ratio", 5.0)]
    row = stock_row(adjusted(bars, actions), "Kotak Mahindra Bank Limited", "Financial Services", None, [])
    assert row["y1"] == pct(443.40, 430.42) == 3.02  # unadjusted: -79.4%
    rebased = adjusted(bars, actions)
    assert rebased[1].high == round(2132.60 * 1.01 / 5, 2) and rebased[1].volume == 5000  # on the new share basis
    assert row["h"] == pytest.approx(443.40 * 1.01) and row["va"] == 5000.0  # unadjusted high: 2,173.62
    unadjusted = stock_row(bars, "Kotak", "", None, [])
    assert unadjusted["y1"] == pct(443.40, 2152.10) and unadjusted["y1"] < -79


@pytest.mark.parametrize(
    "subject, kind, factor",
    [
        (KOTAK_SPLIT, "ratio", 5.0),
        ("Face Value Split (Sub-Division) - From Rs 10/- Per Share To Rs 2/- Per Share", "ratio", 5.0),
        ("Bonus 1:1", "ratio", 2.0),
        ("Bonus 7:5", "ratio", 2.4),
        ("Demerger", "demerger", None),
        ("Scheme Of Arrangement - Bonus Ncrps 46:1", "none", None),  # preference shares: another security
        ("Scheme of Arrangement", "break", None),
        ("Interim Dividend - Rs 2.50 Per Share", "none", None),
        ("Buy Back", "none", None),
    ],
)
def test_each_kind_of_action_in_nses_list(subject, kind, factor):
    assert classify(subject) == (kind, factor)


def demerged_bars(ex_open):
    """A year: 1,000 before a demerger, the ex-date's open from NSE's special pre-open session, then 600."""
    days = [date(2025, 10, 13) + timedelta(days=i) for i in range(251)]
    ex_date = days[100]

    def bar(d):
        close = 1000.0 if d < ex_date else 600.0
        return EquityBar(d, "PARENT", "EQ", close, close * 1.01, close * 0.99, 70, ex_open if d == ex_date else None)

    return [bar(d) for d in days], ex_date


def test_a_demerger_rebases_earlier_prices_on_nses_discovered_ex_date_open():
    bars, ex_date = demerged_bars(ex_open=625.0)  # the market values the parent without its business at 625
    actions = read_corporate_actions(nse_list(("PARENT", f"{ex_date:%d-%b-%Y}", "Demerger")), "list.json")
    rebased = adjusted(bars, actions)
    assert rebased[0].close == 625.0 and rebased[0].volume == 70  # 1,000 / (1,000 / 625); the share count stays
    assert stock_row(rebased, "P", "", None, [])["y1"] == pct(600.0, 625.0)  # not the -40% the raw closes show


def test_a_demerger_without_an_ex_date_trade_or_a_scheme_without_a_ratio_keeps_only_later_sessions():
    bars, ex_date = demerged_bars(ex_open=None)
    for subject in ("Demerger", "Scheme of Arrangement"):
        actions = read_corporate_actions(nse_list(("PARENT", f"{ex_date:%d-%b-%Y}", subject)), "list.json")
        kept = adjusted(bars, actions)
        assert kept[0].day == ex_date and stock_row(kept, "P", "", None, [])["y1"] is None  # no figure, not a wrong one


def test_an_action_after_the_session_is_never_applied():
    bars, ex_date = kotak_bars()
    later = read_corporate_actions(nse_list(("KOTAKBANK", "15-Oct-2026", KOTAK_SPLIT)), "list.json")
    assert on_todays_basis({"KOTAKBANK": bars}, later, date(2026, 10, 12)) == {"KOTAKBANK": bars}


def test_a_list_that_is_not_nses_is_refused():
    with pytest.raises(BadFile):
        read_corporate_actions(b'{"not": "a list"}', "list.json")


def test_only_a_jump_without_a_share_count_action_in_the_list_gets_a_symbol_lookup():
    from fno.market_read_models.corporate_actions import unexplained

    bars, ex_date = kotak_bars()
    etf = [EquityBar(b.day, "BANKNIFTY1", "EQ", b.close, b.high, b.low, b.volume) for b in bars]
    steady = [EquityBar(b.day, "STEADY", "EQ", 100.0, 101.0, 99.0, 10) for b in bars]
    listed = read_corporate_actions(nse_list(("KOTAKBANK", f"{ex_date:%d-%b-%Y}", KOTAK_SPLIT)), "list.json")
    series = {"KOTAKBANK": bars, "BANKNIFTY1": etf, "STEADY": steady}
    assert unexplained(series, listed) == ["BANKNIFTY1"]


def test_a_symbols_own_list_is_filed_per_symbol_and_asked_without_a_date_range():
    from fno.storage.snapshot_source import CorporateActionsBySymbolSource as Own

    path = Own.path_for_symbol(date(2026, 10, 12), "M&M")
    assert path == "nse/equities/corporate-actions-by-symbol/2026/10/12/M&M.json"
    assert Own.day_for_path(path) == date(2026, 10, 12)
    assert Own.url_for(path).endswith("index=equities&symbol=M%26M") and "from_date" not in Own.url_for(path)
