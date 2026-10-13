"""Compares built blocks with the W11 contract's India examples, field by field (story P6, criterion 1). The examples
show pages of the paged blocks, so the route's views are reproduced here exactly as the examples' own builder made them
(dashboard tools/api/examples_screens.py)."""

from __future__ import annotations

from collections.abc import Iterator

from .blocks import default_page
from .stock_rows import UNIVERSE_NIFTY_500

GAINERS_PAGE = 8
INDEX_OPTIONS = ("BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTY")
EXAMPLE_PAGE_KEYS = {  # example name in api/examples/blocks-33-34.json -> page key
    "getScreenerSummaryIndia_india": "screener_summary",
    "getScreenerStocksIndia_india": "screener_stocks",
    "getScreenerStocksIndia_india_high": "screener_stocks",
    "getScreenerStocksIndia_india_gainers": "screener_stocks",
    "getFnoScreenerSummary_india": "fno_screener_summary",
    "getFnoScreenerRows_india": "fno_screener_rows",
    "getFnoScreenerRows_india_index_options": "fno_screener_rows",
    "getOverviewIndicesIndia_india": "overview_indices",
    "getIndiaSectors_india": "overview_sectors",
}


def view(example_name: str, block: dict) -> dict:
    """The served response the example shows, from the published block (the route's default page or query)."""
    rows = block.get("rows")
    if example_name.endswith("_high"):
        high = [r for r in rows if r["h"] and r["p"] >= r["h"] * 0.98]
        return default_page(block, sorted(high, key=lambda r: -(r["p"] - r["l"]) / (r["h"] - r["l"])))
    if example_name.endswith("_gainers"):
        nifty_500 = [r for r in rows if UNIVERSE_NIFTY_500 in r["u"]]
        return default_page(block, sorted(nifty_500, key=lambda r: -r["d1"]), size=GAINERS_PAGE)
    if example_name.endswith("_index_options"):
        index = sorted((r for r in rows if r["s"] in INDEX_OPTIONS), key=lambda r: r["s"])
        return default_page(block, index)
    return default_page(block) if rows is not None else block


def differences(ours, theirs, path: str = "") -> Iterator[tuple[str, object, object]]:
    """Every field where the two payloads differ, as (path, ours, theirs); numbers compare by value (1 == 1.0)."""
    if isinstance(ours, dict) and isinstance(theirs, dict):
        for key in sorted(set(ours) | set(theirs)):
            yield from differences(ours.get(key, "<absent>"), theirs.get(key, "<absent>"), f"{path}.{key}")
    elif isinstance(ours, list) and isinstance(theirs, list) and len(ours) == len(theirs):
        for i, (a, b) in enumerate(zip(ours, theirs)):
            yield from differences(a, b, f"{path}[{i}]")
    elif ours != theirs or type(ours) is bool and type(theirs) is not bool:
        yield path or ".", ours, theirs


def compare(blocks: dict[str, dict], examples: dict) -> dict[str, list[tuple[str, object, object]]]:
    """Example name -> its differences from our blocks (empty: equal field by field)."""
    out = {}
    for name, page_key in EXAMPLE_PAGE_KEYS.items():
        theirs = examples[name]["value"]["payload"]
        out[name] = list(differences(view(name, blocks[page_key]), theirs))
    return out
