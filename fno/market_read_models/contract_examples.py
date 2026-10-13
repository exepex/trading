"""Compares built blocks with the W11 contract's India examples, field by field (story P6, criterion 1). A paged
example is the route's page for its own query (`x-query`), made from our stored table by the contract's route
semantics (screener_route); the other examples are the whole block."""

from __future__ import annotations

from collections.abc import Iterator

from .screener_route import fno_page, stocks_page

QUERY_KEY = "x-query"
OPERATION_PAGE_KEYS = {  # the example's operation (its name before "_india") -> our page key
    "getScreenerSummaryIndia": "screener_summary",
    "getScreenerStocksIndia": "screener_stocks",
    "getFnoScreenerSummary": "fno_screener_summary",
    "getFnoScreenerRows": "fno_screener_rows",
    "getOverviewIndicesIndia": "overview_indices",
    "getIndiaSectors": "overview_sectors",
}
PAGES = {"screener_stocks": stocks_page, "fno_screener_rows": fno_page}
INDIA = "_india"


def page_key(example_name: str) -> str | None:
    """Our page key for an India example of a block we publish, else None (US blocks and other publishers' blocks)."""
    operation, india, _ = example_name.partition(INDIA)
    return OPERATION_PAGE_KEYS.get(operation) if india else None


def view(example: dict, page: str, block: dict) -> dict:
    """The served response the example shows, from the published block."""
    query = example.get(QUERY_KEY)
    return PAGES[page](block, query) if query and page in PAGES else block


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
    """Example name -> its differences from our blocks (empty: equal field by field), for every India example of a
    block we publish."""
    out = {}
    for name, example in examples.items():
        page = page_key(name)
        if page is not None:
            out[name] = list(differences(view(example, page, blocks[page]), example["value"]["payload"]))
    return out
