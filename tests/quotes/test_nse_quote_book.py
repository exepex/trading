"""Story O6, owner's choice (a): the 3 pm recorder on NSE's public option chain. Its quote book comes from the chain
(best bid/ask with sizes, page timestamp, day volume as the same-day trade proof), it records into its own dataset
beside Groww's, and the comparison reports how far the two disagree."""

import json
from datetime import datetime

from fno.models import IST
from fno.providers.nse_quotes import NseQuoteProvider
from fno.quotes.compare import compare_lines
from fno.quotes.recorder import DATASET, NSE_DATASET, QuoteSnapshotRecorder
from fno.quotes.snapshot_rows import VOLUME_PROXY
from fno.storage.raw_store import LocalFolderStore

from .test_quote_recorder import Clock
from .test_recorder_calendar import CALENDAR, TUESDAY

EXPIRIES = ("27-Oct-2026", "24-Nov-2026")


def _leg(expiry: str, strike: int, kind: str, volume: int, bid: float = 100.0) -> dict:
    day = datetime.strptime(expiry, "%d-%b-%Y").strftime("%d-%m-%Y")
    return {
        "expiryDate": day, "strikePrice": strike, "identifier": f"OPTIDXNIFTY{day}{kind}{strike}.00",
        "buyPrice1": bid, "buyQuantity1": 750, "sellPrice1": 101.5, "sellQuantity1": 600, "lastPrice": 100.8,
        "totalTradedVolume": volume, "openInterest": 10, "changeinOpenInterest": 0, "impliedVolatility": 12.0,
    }  # fmt: skip


class FakeNse:
    """NSE's two endpoints as they answered on 13 Oct 2026 (fields trimmed); one strike has no trade today."""

    def __init__(self, bid: float = 100.0):
        self.bid = bid

    def nse_json(self, path: str, params: dict | None = None) -> dict:
        if path == "/api/option-chain-contract-info":
            return {"expiryDates": list(EXPIRIES)}
        expiry = params["expiry"]
        rows = [
            {"strikePrice": k, "CE": _leg(expiry, k, "CE", v, self.bid), "PE": _leg(expiry, k, "PE", v, self.bid)}
            for k, v in ((24900, 5), (25000, 9), (25100, 0))
        ]
        return {"records": {"timestamp": "13-Oct-2026 14:54:30", "underlyingValue": 25000.0, "data": rows}}


def _record(folder, provider, dataset):
    clock = Clock(TUESDAY)
    return QuoteSnapshotRecorder(
        provider, LocalFolderStore(folder), clock.now, clock.sleep, calendar=CALENDAR, dataset=dataset
    ).record()


def test_the_nse_book_gives_bid_ask_sizes_and_the_page_time():
    provider = NseQuoteProvider({}, FakeNse())
    chain = provider.chain("NIFTY", datetime(2026, 10, 27).date())
    book = provider.quote_book(chain, 25000.0, "CE")
    assert (book.bid, book.ask, book.bid_qty, book.ask_qty) == (100.0, 101.5, 750.0, 600.0)
    assert book.quote_time == datetime(2026, 10, 13, 14, 54, 30, tzinfo=IST) and book.traded_today
    assert book.last_trade_time is None and provider.quote_book(chain, 99999.0, "CE") is None


def test_nse_snapshots_go_to_their_own_dataset_with_the_volume_proof(tmp_path):
    result = _record(tmp_path, NseQuoteProvider({}, FakeNse()), NSE_DATASET)
    assert result.status == "recorded" and result.complete
    csv_text = (
        tmp_path / QuoteSnapshotRecorder.path(TUESDAY.date(), f"{result.snapshot_id}.csv", NSE_DATASET)
    ).read_text()
    assert VOLUME_PROXY in csv_text and "2026-10-13T14:54:30+05:30" in csv_text
    assert "no trade today" in csv_text  # the 25100 strike has no volume today: kept, marked invalid
    assert not (tmp_path / DATASET).exists()  # Groww's dataset untouched


def test_the_comparison_reports_both_sources_and_names_a_missing_side(tmp_path):
    assert compare_lines(tmp_path, LocalFolderStore(tmp_path)) == ["no day has a snapshot from either source yet"]
    _record(tmp_path, NseQuoteProvider({}, FakeNse()), NSE_DATASET)
    assert compare_lines(tmp_path, LocalFolderStore(tmp_path)) == [
        "2026-10-13: groww none; nse recorded (no comparison)"
    ]
    _record(tmp_path, NseQuoteProvider({}, FakeNse(bid=100.5)), DATASET)  # stands in for Groww: a tighter book
    assert compare_lines(tmp_path, LocalFolderStore(tmp_path))[0].endswith(
        "contracts groww 12, nse 12; only groww 0, only nse 0; both valid 8: median |mid gap| 0.25, "
        "median spread groww 1.00, nse 1.50"
    )


def test_the_spread_report_reads_groww_only(tmp_path, monkeypatch, capsys):
    import fno.storage.wiring
    from fno.cli import main

    _record(tmp_path, NseQuoteProvider({}, FakeNse()), NSE_DATASET)
    monkeypatch.setattr(fno.storage.wiring, "QUOTES_FOLDER", tmp_path)
    assert main(["quotes", "report"]) == 0
    assert json.loads(capsys.readouterr().out)["days"] == 0  # NSE's snapshot is not in Groww's report
