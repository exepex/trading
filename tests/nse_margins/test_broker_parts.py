"""A14c part 2's parts: the read-only Groww adapter and its allow-list, the basket as Groww's order list, the O9
record (write-once file, receipt, the day's done baskets read back verified), and the Actions jobs never importing the
broker client."""

from datetime import date
from pathlib import Path

import pytest

from fno.intraday.read_only import ReadOnlyGroww, ReadOnlyViolation
from fno.nse_margins.broker_port import BROKER_CHECK_CALLS, BrokerAnswerProblem, GrowwBrokerMargins
from fno.nse_margins.broker_record import BrokerRecord, BrokerResult, RecordProblem, receipt_pathspecs
from fno.storage.data_store import DataStore
from fno.storage.drive_cache import DriveCache
from fno.storage.receipts import ReceiptFolder
from tests.desk.builders import DictStore

from .broker_fakes import BASKETS, at

ROOT = Path(__file__).resolve().parents[2]
DAY = date(2026, 10, 14)


class FakeApi:
    EXCHANGE_NSE, SEGMENT_CASH, SEGMENT_FNO = "NSE", "CASH", "FNO"

    def __init__(self, quote=None, margin=None):
        self.quote = {"payload": {"last_price": 20_050.5}} if quote is None else quote
        self.margin, self.calls = margin or {"span_required": 12_675.0, "exposure_required": 52_130.0}, []

    def get_quote(self, **kwargs):
        self.calls.append(("get_quote", kwargs))
        return self.quote

    def get_order_margin_details(self, **kwargs):
        self.calls.append(("get_order_margin_details", kwargs))
        return self.margin

    def place_order(self, **kwargs):  # pragma: no cover - must be unreachable
        raise AssertionError("an order call reached the SDK")


def test_the_adapter_reads_the_index_and_the_basket_through_its_allow_list():
    api = FakeApi()
    broker = GrowwBrokerMargins(ReadOnlyGroww(lambda: api, BROKER_CHECK_CALLS))
    assert broker.index_level() == 20_050.5
    assert broker.basket(BASKETS[("SF", 100.0)].orders(65)) == (12_675.0, 52_130.0)
    assert api.calls[0][1]["segment"] == "CASH" and api.calls[1][1]["segment"] == "FNO"


@pytest.mark.parametrize(
    ("quote", "margin"),
    [({"payload": {"last_price": 0}}, None), ({}, None), (None, {"span_required": 1.0}), (None, {"error": "x"})],
    ids=["zero level", "no level", "no exposure", "no figures"],
)
def test_an_answer_without_a_usable_figure_is_refused(quote, margin):
    broker = GrowwBrokerMargins(ReadOnlyGroww(lambda: FakeApi(quote, margin), BROKER_CHECK_CALLS))
    with pytest.raises(BrokerAnswerProblem):
        broker.basket([]) if margin else broker.index_level()


def test_this_caller_s_list_meets_the_positive_rule_and_lets_no_other_name_through():
    client = ReadOnlyGroww(lambda: FakeApi(), BROKER_CHECK_CALLS)  # construction applies both rules
    for name in ("place_order", "get_positions_for_user", "get_available_margin_details", "get_order_list"):
        with pytest.raises(ReadOnlyViolation, match=f"{name} is not a read call this client may use"):
            getattr(client, name)
    expected = {"get_order_margin_details", "get_quote", "SEGMENT_FNO", "SEGMENT_CASH", "EXCHANGE_NSE"}
    assert expected == BROKER_CHECK_CALLS


def test_a_basket_is_one_lot_per_leg_at_the_file_s_prices_with_its_side():
    sf = BASKETS[("SF", 100.0)]
    orders = sf.orders(65)
    assert [o["trading_symbol"] for o in orders] == [
        "NIFTY26NOV20000CE", "NIFTY26NOV20000PE", "NIFTY26NOV20100CE", "NIFTY26NOV19900PE"
    ]  # fmt: skip
    assert [o["transaction_type"] for o in orders] == ["SELL", "SELL", "BUY", "BUY"]
    terms = {(o["quantity"], o["order_type"], o["product"], o["exchange"]) for o in orders}
    assert terms == {(65, "LIMIT", "NRML", "NSE")}
    assert [o["price"] for o in orders] == list(sf.prices)
    assert [o["transaction_type"] for o in BASKETS[("BF", 100.0)].orders(65)] == ["BUY", "BUY", "SELL", "SELL"]


def _record(tmp_path, drive=None):
    drive = drive or DictStore()
    receipts = ReceiptFolder(tmp_path / "receipts")
    store = DataStore(drive, "data", receipts, "margins stress-broker-check", "run-1")
    return BrokerRecord(store, DriveCache(drive, receipts, tmp_path / "cache")), drive


def _result(structure, width, status):
    return BrokerResult(at(10, 0), DAY, structure, width, 1.0, 1.0, 2.0, 2.0, status, "")


def test_the_record_is_written_once_with_its_receipt_and_read_back_as_done(tmp_path):
    record, drive = _record(tmp_path)
    path = record.write(DAY, at(10, 0, 5), [_result("SF", 100.0, "ok"), _result("SC", 100.0, "mismatch"),
                                            _result("BF", 100.0, "error")])  # fmt: skip
    assert path == "data/margins/broker_checks/2026-10-14/100005.csv"
    assert (tmp_path / "receipts" / "data/margins/broker_checks/2026-10-14/100005.csv.sha256").is_file()
    assert drive.files[path].decode().splitlines()[0].startswith("checked_at,as_of,structure,width,span_broker_rs")
    assert record.done(DAY) == {("SF", 100.0), ("SC", 100.0)}  # an error is asked again by a same-day rerun
    assert record.done(date(2026, 10, 15)) == set()
    assert receipt_pathspecs() == ("receipts/data/margins/broker_checks/",)


def test_a_damaged_earlier_record_or_a_refused_write_is_a_record_problem(tmp_path):
    record, drive = _record(tmp_path)
    path = record.write(DAY, at(10, 0), [_result("SF", 100.0, "ok")])
    drive.files[path] = b"changed"
    with pytest.raises(RecordProblem, match="cannot be read back"):
        record.done(DAY)

    class Refusing(DictStore):
        def put(self, path, data):
            raise ConnectionError("Drive answered 503")

    refused, _ = _record(tmp_path / "other", Refusing())
    with pytest.raises(RecordProblem, match="was not saved: ConnectionError"):
        refused.write(DAY, at(11, 0), [_result("SF", 100.0, "ok")])


def test_the_root_of_the_jobs_github_actions_runs_builds_no_broker_client():
    """Actions holds no Groww key: only `broker_wiring.py` builds the Groww client and the broker check."""
    source = (ROOT / "fno" / "nse_margins" / "wiring.py").read_text(encoding="utf-8")
    assert "GrowwProvider" not in source and "broker_" not in source.replace("broker_approvals", "")
    workflows = " ".join(p.read_text(encoding="utf-8") for p in (ROOT / ".github" / "workflows").glob("*.yml"))
    assert "stress-broker-check" not in workflows


def test_the_wiring_gives_the_check_only_this_caller_s_read_only_client(monkeypatch):
    from fno.config import load_app_config
    from fno.nse_margins import broker_wiring

    class Provider:
        def __init__(self, cfg):
            self.api = FakeApi()

    monkeypatch.setattr(broker_wiring, "GrowwProvider", Provider)
    monkeypatch.setattr(broker_wiring, "build_drive_span_files", lambda env: lambda day: ("x", None))
    monkeypatch.setattr(broker_wiring, "build_data_store", lambda writer, env: ("store", writer))
    monkeypatch.setattr(broker_wiring, "build_drive_cache", lambda env: "cache")
    check = broker_wiring.build_broker_check(load_app_config(), env={})
    assert check.pace_seconds == 2.0 and check.parts.record.store == ("store", "margins stress-broker-check")
    client = check.parts.broker.client
    assert client.get_quote and client.SEGMENT_FNO == "FNO"
    with pytest.raises(ReadOnlyViolation):
        client.place_order  # noqa: B018
