"""Story E7: expired legs are cash-settled at intrinsic value against NSE's final settlement price (the expiry day's
F&O file only), with C1's settlement charges; until the file is published the trade is `settlement_needed` and blocks
the book; once settled, C2 no longer sees the position and C1's ledgers agree with the account to the paisa."""

import csv
import io
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.accounting.ledgers import trade_line
from fno.books.account import PaperAccount
from fno.books.equity import MissingMark
from fno.constants import (
    BOOK1_RULES,
    FILL_SETTLE,
    LEDGER_SETTLEMENT,
    OPTION_CALL,
    OPTION_PUT,
    OUTCOME_CLOSED,
    OUTCOME_NOT_OPENED,
    OUTCOME_OPENED,
    OUTCOME_SETTLEMENT_NEEDED,
)
from fno.desk.records import DeskRecords
from fno.desk.settlement import NseFinalSettlement, SettlementError
from fno.desk.wiring import open_desk_journal
from fno.research_engine.structures import Leg
from fno.risk.book_view import load_risk_book
from fno.storage.raw_library import RawFileLibrary
from fno.storage.raw_source import NseDailyFoSource
from fno.storage.raw_store import LocalFolderStore

from .builders import (
    CHARGES,
    DAY,
    EXPIRY,
    LOT,
    at,
    contract,
    decision_market,
    enter,
    fly_order,
    fly_rows,
    write_snapshot,
)

CE, PE = OPTION_CALL, OPTION_PUT
REAL = Path(__file__).parent.parent / "fixtures" / "nse_settlement"  # NSE's 25 Jan 2024 file, NIFTY rows cut out
AFTER = EXPIRY + timedelta(days=1)


class Unpublished:
    """The original source: publishes nothing (a file not in the store is not out yet)."""

    name = "nse"

    def fetch(self, path):
        return None


class AskedStore(LocalFolderStore):
    def __init__(self, folder):
        super().__init__(folder)
        self.asked = []

    def get(self, path):
        self.asked.append(path)
        return super().get(path)


def nse(folder=REAL):
    store = AskedStore(folder)
    return NseFinalSettlement(RawFileLibrary([store], Unpublished())), store


def test_the_final_settlement_price_comes_from_the_expiry_day_s_file_only():
    reader, store = nse()
    final = reader.final_settlement("NIFTY", date(2024, 1, 25))
    assert final.price == 21352.60  # every expiring row agrees: the future and each option's SttlmPric
    assert store.asked == [NseDailyFoSource.path_for(date(2024, 1, 25))] and final.source == store.asked[0]
    assert len(final.sha256) == 64


def tampered(tmp_path, change) -> Path:
    """A copy of the real file with `change(rows)` applied, at the same archive path."""
    path = NseDailyFoSource.path_for(date(2024, 1, 25))
    name = path.rsplit("/", 1)[-1]
    with zipfile.ZipFile(REAL / path) as original:
        rows = list(csv.DictReader(io.StringIO(original.read(name[:-4]).decode())))
    fields = list(rows[0])
    change(rows)
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (tmp_path / path).parent.mkdir(parents=True)
    with zipfile.ZipFile(tmp_path / path, "w") as copy:
        copy.writestr(name[:-4], out.getvalue())
    return tmp_path


def test_an_unpublished_file_gives_no_price(tmp_path):
    reader, _ = nse(tmp_path)
    assert reader.final_settlement("NIFTY", date(2024, 1, 25)) is None


def test_a_file_without_one_clear_price_is_refused_never_guessed(tmp_path):
    def disagree(rows):
        rows[-1]["SttlmPric"] = "21400.00"

    reader, _ = nse(tampered(tmp_path / "a", disagree))
    with pytest.raises(SettlementError, match="disagree"):
        reader.final_settlement("NIFTY", date(2024, 1, 25))

    def none_expiring(rows):
        rows[:] = [r for r in rows if r["XpryDt"] != "2024-01-25"]

    reader, _ = nse(tampered(tmp_path / "b", none_expiring))
    with pytest.raises(SettlementError, match="no expiring contracts"):
        reader.final_settlement("NIFTY", date(2024, 1, 25))


def test_the_real_file_shows_why_the_close_is_never_used():
    """NSE's 25 Jan 2024 file: the 21300 CE closed at 19.70 while it settled 52.60 in the money."""
    path = NseDailyFoSource.path_for(date(2024, 1, 25))
    with zipfile.ZipFile(REAL / path) as original:
        rows = list(csv.DictReader(io.StringIO(original.read(original.namelist()[0]).decode())))
    row = next(r for r in rows if r["OptnTp"] == "CE" and float(r["StrkPric"]) == 21300 and r["XpryDt"] == "2024-01-25")
    assert (float(row["ClsPric"]), float(row["SttlmPric"])) == (19.70, 21352.60)
    assert Leg(21300, "CE", 1).intrinsic(float(row["SttlmPric"])) == pytest.approx(52.60)


def review_after_expiry(root, store, snapshots, exit_desk, clock):
    write_snapshot(store, "after", fly_rows(), at(15, 15, day=AFTER), at(15, 15, 40, day=AFTER), day=AFTER)
    clock.set(at(15, 20, day=AFTER))
    with open_desk_journal(BOOK1_RULES, root) as journal:
        return exit_desk.review(BOOK1_RULES, snapshots.snapshot(AFTER, "after"), journal, {})


@pytest.fixture
def opened(root, store, snapshots, entry_desk):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    assert enter(root, snapshots, entry_desk, fly_order()).outcome == OUTCOME_OPENED
    return PaperAccount(root, BOOK1_RULES).summary()["open_trades"][0]["cash_flow_rs"]


def settled(root):
    rows = DeskRecords(PaperAccount(root, BOOK1_RULES)).fill_rows()
    return {r["contract"]: (r["side"], float(r["price"]), float(r["charges_rs"])) for r in rows
            if r["action"] == FILL_SETTLE}  # fmt: skip


def test_an_itm_short_settles_at_intrinsic_value_not_its_stale_mid(root, store, snapshots, exit_desk, clock,
                                                                   settlements, opened):  # fmt: skip
    settlements.prices[EXPIRY] = 25100.0  # the short 25000 CE ends 100 in the money; every other leg worthless
    [result] = review_after_expiry(root, store, snapshots, exit_desk, clock)
    brokerage = CHARGES["brokerage_per_order"] * (1 + CHARGES["gst_pct"] / 100)  # Rs 23.60; a short pays no STT
    assert settled(root) == {
        contract(25000, CE): ("buy", 100.0, pytest.approx(brokerage)),  # never the pre-expiry mid of 150.50
        contract(25000, PE): ("buy", 0.0, 0.0),
        contract(25200, CE): ("sell", 0.0, 0.0),
        contract(24800, PE): ("sell", 0.0, 0.0),
    }
    net = opened - 100.0 * LOT - brokerage
    assert result.outcome == OUTCOME_CLOSED and result.reason.endswith(f"net Rs {net:,.2f}")
    assert "settled at NSE's final settlement price 25,100.00" in result.reason


def test_out_of_the_money_legs_settle_at_zero_with_no_charges(root, store, snapshots, exit_desk, clock, settlements,
                                                              opened):  # fmt: skip
    settlements.prices[EXPIRY] = 25000.0  # pinned at the short strike: all four legs worthless
    [result] = review_after_expiry(root, store, snapshots, exit_desk, clock)
    assert {price for _, price, _ in settled(root).values()} == {0.0}
    assert {charge for *_, charge in settled(root).values()} == {0.0}
    assert result.outcome == OUTCOME_CLOSED and result.reason.endswith(f"net Rs {opened:,.2f}")  # the credit is kept


def test_an_itm_long_pays_exercise_stt_on_its_intrinsic_value(root, store, snapshots, exit_desk, clock, settlements,
                                                              opened):  # fmt: skip
    settlements.prices[EXPIRY] = 25300.0  # short 25000 CE: 300 in the money; long 25200 CE: 100
    review_after_expiry(root, store, snapshots, exit_desk, clock)
    brokerage = CHARGES["brokerage_per_order"] * (1 + CHARGES["gst_pct"] / 100)
    stt = 100.0 * LOT * CHARGES["stt_exercise_pct"] / 100  # 0.15% of Rs 6,500 = Rs 9.75
    assert CHARGES["stt_exercise_pct"] == 0.15 and stt == pytest.approx(9.75)
    assert settled(root)[contract(25200, CE)] == ("sell", 100.0, pytest.approx(brokerage + stt))
    assert settled(root)[contract(25000, CE)] == ("buy", 300.0, pytest.approx(brokerage))


def test_a_missing_settlement_file_blocks_new_risk_until_published(root, store, snapshots, entry_desk, exit_desk,
                                                                   clock, alerts, settlements, opened):  # fmt: skip
    [result] = review_after_expiry(root, store, snapshots, exit_desk, clock)
    assert result.outcome == OUTCOME_SETTLEMENT_NEEDED and "is not published yet" in result.reason
    assert len(alerts.sent) == 1 and settled(root) == {}
    blocked = enter(root, snapshots, entry_desk, fly_order("t2", decided_at=at(15, 5, day=AFTER)), "after", AFTER)
    assert blocked.outcome == OUTCOME_NOT_OPENED and "(settlement_needed) blocks new risk" in blocked.reason
    settlements.prices[EXPIRY] = 25000.0  # the file is published by the next review
    [result] = review_after_expiry(root, store, snapshots, exit_desk, clock)
    assert result.outcome == OUTCOME_CLOSED
    assert settlements.asked == [("NIFTY", EXPIRY)] * 2  # the expiry day's settlement only


def test_settlement_releases_c2_s_view_and_c1_s_ledger_agrees_with_the_account(root, store, snapshots, exit_desk,
                                                                               clock, settlements, opened):  # fmt: skip
    market = decision_market(day=AFTER)
    account = PaperAccount(root, BOOK1_RULES)
    with pytest.raises(MissingMark):  # before settlement the dead contracts still need marks
        account.state({})
    settlements.prices[EXPIRY] = 25300.0
    review_after_expiry(root, store, snapshots, exit_desk, clock)
    assert load_risk_book(root, BOOK1_RULES, market, {}).open_trades == ()  # nothing left for C2's limits
    assert account.state({}).open_trades == 0
    [trade] = account.closed_trades()
    net = account.summary()["closed_trades"][0]["net_rs"]
    assert trade_line(trade, CHARGES).net == pytest.approx(net, abs=1e-9)  # one charges model for both
    kinds = [row["kind"] for row in account.ledger_rows()]
    assert kinds.count(LEDGER_SETTLEMENT) == 4 and DAY < trade.closed_on == EXPIRY
