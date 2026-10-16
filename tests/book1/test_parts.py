"""Story E5's parts: Book 1's market from the canonical snapshot, its inputs refused unless the snapshot is the one the
common pack records, the trade terms read back from its records, and its exit rules from the playbook version."""

import hashlib
import json
from datetime import date, datetime

import pytest

from fno.books.book1_inputs import InputsRefused, LiveBook1Inputs
from fno.books.book1_market import NoMarket, market_from_snapshot
from fno.books.book1_records import recorded_terms
from fno.constants import BOOK1_RULES
from fno.desk.common_pack import SNAPSHOT_INPUT, CommonPack
from fno.desk.pack_store import PackStore
from fno.desk.private_pack import PrivatePack
from fno.playbook.decision_store import SUMS_FILE, DecisionStore
from fno.playbook.exit_terms import unenforceable_exits
from fno.playbook.opportunities import OpportunityFinder
from fno.playbook.schema import parse_strategy
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.research_data.panel_reader import FutureQuote
from fno.research_data.quote_snapshots import CutoffSnapshot, LiveQuote
from fno.research_engine.cycles import TradingDays
from fno.research_engine.implied_vol import Black76, OptionPricing
from fno.risk.inputs import TradeTerms
from fno.storage.raw_store import LocalFolderStore
from tests.checks.builders import CALENDAR
from tests.decisions.builders import doc
from tests.desk.builders import fly_rows, write_snapshot

from .builders import EXITS, book1_doc
from .openings import open_trades

DAY, EXPIRY = date(2026, 10, 13), date(2026, 11, 24)


def cutoff(quotes, spot=25_000.0, future=25_080.0):
    return CutoffSnapshot(DAY, datetime(2026, 10, 13, 15, 0), spot, 12.0, tuple(quotes),
                          (FutureQuote(EXPIRY, future, 0.0, 1000, 0),))  # fmt: skip


def test_the_market_holds_only_valid_named_quotes_at_their_mid_with_a_black76_iv():
    quotes = [LiveQuote(EXPIRY, 25_000, "CE", 300.0, 302.0, True, "N25000CE"),
              LiveQuote(EXPIRY, 25_000, "PE", 220.0, 222.0, False, "N25000PE"),  # not valid by A4
              LiveQuote(EXPIRY, 25_200, "CE", 200.0, 202.0, True, ""),  # no recorded symbol
              LiveQuote(EXPIRY, 24_000, "CE", 900.0, 902.0, True, "N24000CE")]  # below intrinsic: no IV  # fmt: skip
    market = market_from_snapshot(DAY, cutoff(quotes), 0.065, Black76())
    assert list(market.quotes) == ["N25000CE"] and market.quotes["N25000CE"].mid == 301.0
    assert 0.05 < market.quotes["N25000CE"].iv < 0.5 and market.spot == 25_000.0 and EXPIRY in market.futures
    years = (EXPIRY - DAY).days / 365
    on_future = Black76().implied_vol(OptionPricing(301.0, 25_080.0, 25_000, "CE", years, 0.065))
    on_spot = Black76().implied_vol(OptionPricing(301.0, 25_000.0, 25_000, "CE", years, 0.065))
    assert market.quotes["N25000CE"].iv == on_future != on_spot  # Black-76 on the same-expiry future, not spot
    with pytest.raises(NoMarket):
        market_from_snapshot(DAY, cutoff(quotes, spot=None), 0.065, Black76())


def write_packs(root, day, snapshot_id, csv_sha, private=True, meta_sha=None):
    """The packs as E2 writes them; `meta_sha`: the sidecar's hash, which the pack records beside the quote file's."""
    store = PackStore(root)
    recorded = {"snapshot_id": snapshot_id, "csv_sha256": csv_sha, "meta_sha256": meta_sha}
    body = {"day": day.isoformat(), "provenance": {SNAPSHOT_INPUT: recorded}, "items": []}
    store.write_common(CommonPack(day, body))
    if private:
        store.write_private(PrivatePack(BOOK1_RULES, day, {"day": day.isoformat(), "book": BOOK1_RULES}))


def test_inputs_are_refused_unless_the_snapshot_is_the_one_the_pack_records(tmp_path):
    quotes = LocalFolderStore(tmp_path / "quotes")
    write_snapshot(quotes, "canon", fly_rows(), datetime(2026, 10, 13, 14, 56), datetime(2026, 10, 13, 14, 57), day=DAY)
    quotes.put(QuoteSnapshotRecorder.path(DAY, f"nifty_{DAY:%Y%m%d}.canonical"), b"canon")
    inputs = LiveBook1Inputs(tmp_path, quotes, 0.065, Black76(), lambda d, s: None, lambda m: (None, None, None),
                             lambda d, h: dict(h))  # fmt: skip
    with pytest.raises(InputsRefused, match="no common pack"):
        inputs.day(DAY)
    write_packs(tmp_path / "other", DAY, "canon", "0" * 64)  # the pack froze another file
    inputs.root = tmp_path / "other"
    with pytest.raises(InputsRefused, match="not the one its common pack records"):
        inputs.day(DAY)
    sha = hashlib.sha256(quotes.get(QuoteSnapshotRecorder.path(DAY, "canon.csv"))).hexdigest()
    write_packs(tmp_path, DAY, "canon", sha, private=False)  # the right snapshot, but no private pack
    inputs.root = tmp_path
    with pytest.raises(InputsRefused, match="private.json of 2026-10-13 is missing"):
        inputs.day(DAY)


def test_the_trade_terms_of_book1_s_trades_come_from_its_committed_records(tmp_path):
    run = DecisionStore(tmp_path, BOOK1_RULES).day_folder(DAY) / "2026-10-13-r1"
    run.mkdir(parents=True)
    trade = {"trade_id": "t1", "structure": "SC", "width": 200, "lots": 1}
    opportunity = "sc-a-v1:2026-11-24"
    (run / "a.json").write_text(
        json.dumps({"chosen_action": "trade", "structure": trade, "opportunity_id": opportunity})
    )
    no_trade = {"chosen_action": "no trade", "structure": {**trade, "trade_id": "t2"}, "opportunity_id": opportunity}
    (run / "b.json").write_text(json.dumps(no_trade))
    sums = "".join(f"{hashlib.sha256((run / n).read_bytes()).hexdigest()}  {n}\n" for n in ("a.json", "b.json"))
    (run / SUMS_FILE).write_text(sums)
    open_trades(tmp_path, BOOK1_RULES, DAY, run.name, "c1", ["t1", "t2"])  # story D3b: filled trades only
    assert recorded_terms(tmp_path, BOOK1_RULES) == {"t1": TradeTerms("SC", 200, 1)}


def test_the_exit_is_the_version_s_time_exit_as_d2_computed_it():
    strategy = parse_strategy(book1_doc())
    finder = OpportunityFinder(TradingDays(CALENDAR))
    exit_day = finder.exit_day(strategy, EXPIRY)
    assert exit_day == date(2026, 11, 3)  # the last session on or before 24 Nov - 21 days (3 Nov, a Tuesday)
    assert finder.exit_day(strategy, date(2026, 11, 10)) == date(2026, 10, 19)  # 20 Oct is a holiday (Dussehra)
    assert unenforceable_exits(parse_strategy(doc("sc-b", exits={**EXITS, "loss": "stop at 2x credit"}))) == [
        "loss: stop at 2x credit"]  # fmt: skip


def test_the_time_exit_fires_on_its_day_and_not_before():
    from fno.desk.exit_rules import ExitContext, ExitOnDay

    rule = ExitOnDay(date(2026, 11, 3), "sc-a-v1 time exit")
    assert rule.reached(None, ExitContext(date(2026, 11, 2), None)) == ""
    assert rule.reached(None, ExitContext(date(2026, 11, 3), None)).startswith("time_exit: 2026-11-03 is on or after")


def test_the_order_replay_holds_c4_s_validator_and_writes_no_failure_log(tmp_path):
    """Judge 84 C: the orders replay with C4's validator (else every run differs), built with log=False so a replay
    writes nothing; the decision run's own validator does log."""
    from fno.books.book1_wiring import build_book1_orders
    from fno.checks.validity_adapter import BookTradeValidator
    from fno.config import load_app_config
    from fno.playbook.wiring import build_decision_run

    orders = build_book1_orders(load_app_config(), tmp_path)
    assert isinstance(orders.validator, BookTradeValidator) and orders.validator.log is None
    assert build_decision_run(load_app_config(), BOOK1_RULES, tmp_path).validator.log is not None
