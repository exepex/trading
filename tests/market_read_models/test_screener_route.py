"""Story P6, judge 49 minor 1: the comparison serves each W11 example from our stored table by its own query
(`x-query`), with the contract's route semantics (filters, sorts, ties, pages), for every India block we publish."""

from fno.market_read_models.contract import PinnedContract
from fno.market_read_models.contract_examples import compare, page_key, view
from fno.market_read_models.screener_route import fno_page, stocks_page
from fno.market_read_models.wiring import CONTRACT_FOLDER

TABLE = {"as_of": "2026-10-12T10:00:00Z", "currency": "INR"}


def stock(s, p, v, d1=0.0, u=("n500",), h=None, l=None, r=None, m1=None, va=1.0, dl=None):  # noqa: E741
    return {"s": s, "p": p, "v": v, "d1": d1, "u": list(u), "h": h, "l": l, "r": r, "m1": m1, "va": va, "dl": dl}


def test_the_examples_compared_are_every_india_example_of_a_block_we_publish():
    names = [n for n in PinnedContract(CONTRACT_FOLDER).examples() if page_key(n)]
    assert len(names) == 21 and not any("_us" in n for n in names)  # 8 before the pin moved, 13 new (d7c982a)
    assert page_key("getScreenerStocksUs_us") is None and page_key("getIndiaSectors_india") == "overview_sectors"


def test_a_sort_puts_missing_values_last_and_breaks_ties_by_value_traded_then_symbol():
    rows = [stock("A", 10, 1, d1=2.0), stock("B", 10, 5, d1=2.0), stock("C", 10, 5, d1=None), stock("D", 1, 50)]
    page = stocks_page({**TABLE, "rows": rows}, {"u": "all", "sort": "d1", "page": 1, "page_size": 3})
    assert [r["s"] for r in page["rows"]] == ["B", "A", "D"] and page["total"] == 4  # D: 0.0; C: no change, last
    ascending = stocks_page({**TABLE, "rows": rows}, {"u": "all", "sort": "-d1", "page": 2, "page_size": 3})
    assert [r["s"] for r in ascending["rows"]] == ["C"]


def test_universe_screen_and_filters_select_the_rows():
    rows = [
        stock("LOW", 50, 1, u=(), r=25.0), stock("OVERSOLD", 200, 1, r=20.0, m1=6.0, dl=65.0),
        stock("HIGH", 200, 1, h=201.0, l=100.0, r=70.0, m1=4.0),
    ]  # fmt: skip
    oversold = stocks_page(
        {**TABLE, "rows": rows}, {"u": "n500", "screen": "oversold", "sort": "-r", "page": 1, "page_size": 25}
    )
    assert [r["s"] for r in oversold["rows"]] == ["OVERSOLD"]  # LOW is not in the Nifty 500
    filters = {
        "u": "all",
        "period": "m1",
        "pmin": 100,
        "cmin": 5,
        "dlmin": 60,
        "sort": "value",
        "page": 1,
        "page_size": 25,
    }
    assert [r["s"] for r in stocks_page({**TABLE, "rows": rows}, filters)["rows"]] == ["OVERSOLD"]


def test_fno_screens_and_symbols():
    rows = [
        {"s": "NIFTY", "kind": "index", "b": "long_buildup", "oi": 10, "fut": 100.0, "ivr": 50, "oc": 1.0},
        {"s": "DMART", "kind": "stock", "b": "short_buildup", "oi": 5, "fut": 10.0, "ivr": 90, "oc": 7.0},
    ]
    assert [
        r["s"]
        for r in fno_page({**TABLE, "rows": rows}, {"screen": "ivhigh", "sort": "ivr", "page": 1, "page_size": 25})[
            "rows"
        ]
    ] == ["DMART"]  # noqa: E501
    by_symbol = fno_page({**TABLE, "rows": rows}, {"symbols": ["NIFTY"], "sort": "oi", "page": 1, "page_size": 25})
    assert [r["s"] for r in by_symbol["rows"]] == ["NIFTY"]


def test_an_example_with_a_query_is_compared_on_its_page_and_one_without_on_the_whole_block():
    table = {**TABLE, "total": 2, "rows": [stock("A", 10, 1), stock("B", 20, 1)]}
    example = {"x-query": {"u": "all", "sort": "value", "page": 1, "page_size": 1}}
    assert view(example, "screener_stocks", table)["rows"] == [table["rows"][1]]
    assert view({}, "overview_sectors", {"indices": []}) == {"indices": []}
    served = {**view(example, "screener_stocks", table)}
    found = compare(
        {"screener_stocks": table}, {"getScreenerStocksIndia_india": {**example, "value": {"payload": served}}}
    )
    assert found == {"getScreenerStocksIndia_india": []}
