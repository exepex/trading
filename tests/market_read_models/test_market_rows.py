"""Story P6: the rows each block is built from, on small NSE-shaped inputs with hand-checked answers."""

import io
import zipfile
from datetime import date, timedelta

import pytest

from fno.fo_bhavcopy import BadFile
from fno.market_read_models.fno_rows import FnoRowBuilder, buildup, underlying_days
from fno.market_read_models.index_rows import index_rows, industries
from fno.market_read_models.nse_files import (
    EquityBar,
    IndexFigures,
    read_delivery,
    read_equity_bhavcopy,
    read_index_figures,
)
from fno.market_read_models.stock_rows import pct, rsi14, stock_rows, stock_series
from fno.research_engine.implied_vol import SpotBlackScholes
from fno.storage.raw_source import NseDeliverySource, NseEquityBhavcopySource
from fno.storage.snapshot_source import EquityListSource

DAY = date(2026, 10, 12)


def zipped(name: str, text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, text)
    return buffer.getvalue()


def test_the_equity_file_keeps_eq_and_be_rows_and_a_wrong_file_is_refused():
    text = (
        "TradDt,TckrSymb,SctySrs,ClsPric,HghPric,LwPric,TtlTradgVol\n"
        "2026-10-12,ABC,EQ,10.5,11,10,1200\n2026-10-12,GOLD,GB,1,1,1,1\n2026-10-12,XYZ,BE,5,5,4,7.0\n"
    )
    name = NseEquityBhavcopySource.filename_for(DAY)
    bars = read_equity_bhavcopy(zipped("x.csv", text), name)
    assert bars == [EquityBar(DAY, "ABC", "EQ", 10.5, 11.0, 10.0, 1200), EquityBar(DAY, "XYZ", "BE", 5.0, 5.0, 4.0, 7)]
    with pytest.raises(BadFile):
        read_equity_bhavcopy(zipped("x.csv", "a,b\n1,2\n"), name)


def test_delivery_reads_nse_padded_columns_and_its_dash_for_no_figure():
    text = "SYMBOL, SERIES, DELIV_PER\nABC, EQ, 39.80\nXYZ, BE, -\nBOND, GB, 10\n"
    assert read_delivery(text.encode(), NseDeliverySource.filename_for(DAY)) == {"ABC": 39.8, "XYZ": None}


def test_index_figures_keep_pe_pb_and_yield_and_skip_rows_without_a_close():
    text = (
        "Index Name,Closing Index Value,P/E,P/B,Div Yield\n"
        "Nifty 50,22363.35,19.12,2.75,1.53\nIndia VIX,15.2,-,-,-\nOdd Index,-,1,1,1\n"
    )
    figures = read_index_figures(text.encode(), "ind_close_all_12102026.csv")
    assert figures == {
        "Nifty 50": IndexFigures(22363.35, 19.12, 2.75, 1.53),
        "India VIX": IndexFigures(15.2, None, None, None),
    }


def test_rsi_and_period_changes_follow_the_contracts_formulas():
    assert rsi14([float(x) for x in range(1, 16)]) == 100.0  # only gains
    assert rsi14([10.0] * 14) is None  # needs 15 closes
    assert pct(110.0, 100.0) == 10.0 and pct(1.0, None) is None and pct(1.0, 0.0) is None


def bars(symbol: str, closes: list[float], volume: int = 100) -> list[EquityBar]:
    start = DAY - timedelta(days=len(closes) - 1)
    return [EquityBar(start + timedelta(days=i), symbol, "EQ", c, c + 1, c - 1, volume) for i, c in enumerate(closes)]


def test_a_stock_row_from_its_series():
    series = stock_series([[b] for b in bars("ABC", [100.0 + i for i in range(30)], volume=50)])
    series["OLD"] = bars("OLD", [5.0, 6.0])[:1]  # did not trade on the day: no row
    (row,) = stock_rows(series, DAY, {"ABC": "Abc Ltd"}, {"ABC": "Banks"}, {"ABC": 40.0}, {"ABC"})
    assert row["s"] == "ABC" and row["n"] == "Abc Ltd" and row["g"] == "Banks" and row["p"] == 129.0
    assert row["d1"] == pct(129.0, 128.0) and row["w1"] == pct(129.0, 124.0) and row["m1"] == pct(129.0, 108.0)
    assert row["m3"] is None and row["y1"] is None  # fewer sessions than 63 and 250
    assert (row["h"], row["l"], row["v"], row["va"], row["dl"]) == (130.0, 99.0, 50, 50.0, 40.0)
    assert row["u"] == ["n500", "fno"]


def test_an_industry_counts_only_for_a_company_on_nses_list():
    series = stock_series([bars("ABC", [1.0, 2.0])])
    (row,) = stock_rows(series, DAY, {}, {"ABC": "Banks"}, {}, set())
    assert row["n"] == "ABC" and row["g"] == "" and row["u"] == []


def fo_row(kind, expiry, strike="", option="", close="10", prev="", oi="1000", change="0", volume="5", spot="100"):
    return {"TckrSymb": "ABC", "FinInstrmTp": kind, "XpryDt": expiry, "StrkPric": strike, "OptnTp": option,
            "ClsPric": close, "PrvsClsgPric": prev, "OpnIntrst": oi, "ChngInOpnIntrst": change, "TtlTradgVol": volume,
            "UndrlygPric": spot, "NewBrdLotQty": "50"}  # fmt: skip


def test_an_underlying_uses_its_nearest_monthly_expiry_and_the_strike_nearest_the_spot():
    rows = [
        fo_row("STF", "2026-10-27", close="101", prev="100", oi="1100", change="100"),
        fo_row("STF", "2026-11-24", close="102", prev="100"),
        fo_row("STO", "2026-10-20", "100", "CE"),  # a weekly expiry: not the month's last
        fo_row("STO", "2026-10-27", "100", "CE", close="4", volume="9", oi="300"),
        fo_row("STO", "2026-10-27", "100", "PE", close="3.5", volume="0", oi="600"),
        fo_row("STO", "2026-10-27", "110", "CE", close="1", oi="50"),
    ]
    (u,) = underlying_days(DAY, rows)
    assert (u.expiry, u.atm, u.call_oi, u.put_oi, u.kind, u.lot) == (date(2026, 10, 27), 100.0, 350, 600, "stock", 50)
    row = FnoRowBuilder(SpotBlackScholes(), 0.065).row([u], {"ABC": "Abc Ltd"})
    assert (row["fc"], row["oi"], row["oc"], row["b"]) == (1.0, 1100, 10.0, "long_buildup")
    assert row["pcr"] == round(600 / 350, 2) and row["mv"] == 7.5 and row["x"] == "2026-10-27"
    assert row["iv"] is not None and row["ivr"] is None  # the put did not trade: the call's IV alone; one day: no rank


@pytest.mark.parametrize(
    "price, oi, expected",
    [(1, 1, "long_buildup"), (-1, 1, "short_buildup"), (1, -1, "short_covering"), (-1, -1, "long_unwinding")],
)
def test_the_futures_buildup_reading(price, oi, expected):
    assert buildup(price, oi) == expected


def test_index_rows_put_broad_and_vix_first_and_date_an_index_by_its_own_last_figure():
    def figures(close):
        return IndexFigures(close, None, None, None)

    sessions = [
        (date(2026, 10, 8), {"Nifty 50": figures(100.0), "Nifty IT": figures(10.0), "India VIX": figures(15.0)}),
        (date(2026, 10, 9), {"Nifty 50": figures(101.0), "Nifty IT": figures(11.0), "India VIX": figures(14.0)}),
        (date(2026, 10, 12), {"Nifty 50": figures(102.0), "India VIX": figures(13.0)}),  # Nifty IT missing that day
    ]
    rows = index_rows(sessions)
    assert [r["name"] for r in rows] == ["Nifty 50", "India VIX", "Nifty IT"]
    assert rows[2]["as_of"] == "2026-10-09" and rows[2]["close"] == 11.0  # never passed off as the 12th's close
    assert rows[0]["d1"] == pct(102.0, 101.0) and rows[0]["group"] == "broad" and rows[1]["group"] == "vol"


def test_industries_are_equal_weighted_with_their_best_and_worst_stock():
    stocks = [{"s": "A", "g": "Banks", "d1": 2.0, "w1": 1.0, "m1": None, "m3": 1.0, "y1": 1.0},
              {"s": "B", "g": "Banks", "d1": -1.0, "w1": 3.0, "m1": None, "m3": 1.0, "y1": 1.0},
              {"s": "C", "g": "", "d1": 9.0, "w1": 1.0, "m1": 1.0, "m3": 1.0, "y1": 1.0}]  # fmt: skip
    (banks,) = industries(stocks)
    assert (banks["n"], banks["d1"], banks["w1"], banks["m1"]) == (2, 0.5, 2.0, None)
    assert (banks["up"], banks["down"], banks["best"], banks["worst"]) == (1, 1, ["A", 2.0], ["B", -1.0])


def test_a_reference_list_snapshot_is_filed_under_its_day_with_its_original_name():
    path = EquityListSource.path_for(DAY)
    assert path == "nse/equities/equity-list/2026/10/12/EQUITY_L.csv"
    assert EquityListSource.day_for_path(path) == DAY
    with pytest.raises(ValueError):
        EquityListSource.day_for_path("nse/equities/equity-list/2026/10/12/OTHER.csv")
