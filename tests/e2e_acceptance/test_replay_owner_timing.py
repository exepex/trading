"""Story O11's E8 check (replacing its strict xfail): 16 Oct 2026 replayed with E8 live from that day. The daily run
hands Book 1's trade over to the owner-timing fill (R = 60, the verdict) instead of filling it at 15:15: no leg is
filled, the order is kept as decided, and the trade waits for E8's step, which runs right after the quote parts."""

from fno.books.account import PaperAccount
from fno.constants import (
    BOOK1_RULES,
    DAILY_RUN_STEPS,
    OUTCOME_ENTRY_PENDING,
    OWNER_TIMING_STEP,
    VERDICT_REACTION_MINUTES,
)
from fno.daily.wiring import LIVE_STEPS
from fno.desk.entries import EntryDesk
from fno.desk.owner_timing.live_switch import LiveFromEntries
from fno.desk.owner_timing.order_record import KeptOrders
from fno.desk.owner_timing.pending import pending_entries
from fno.desk.owner_timing.pending_entries import HANDED_OVER, PendingEntries
from fno.desk.records import DeskRecords
from tests.desk.builders import CHARGES, DictStore
from tests.desk.conftest import RecordingAlerts

from . import real_day as rd
from .replay import Replay


def test_e8_is_wired_after_the_quote_parts_at_the_verdict_reaction_time():
    steps = list(DAILY_RUN_STEPS)
    assert VERDICT_REACTION_MINUTES == 60 and OWNER_TIMING_STEP in LIVE_STEPS
    assert steps.index(OWNER_TIMING_STEP) == steps.index("quotes") + 1


def test_live_from_the_day_the_trade_is_handed_over_not_filled_at_the_snapshot(tmp_path, monkeypatch):
    orders = DictStore()
    hand_over = lambda clock: LiveFromEntries(  # noqa: E731
        rd.DAY, EntryDesk(CHARGES, clock), PendingEntries(VERDICT_REACTION_MINUTES, KeptOrders(orders, orders))
    )
    alerts = RecordingAlerts()
    log = Replay(tmp_path, monkeypatch, alerts, entries=hand_over).run().log
    [(trade_id, fill)] = log.result("fills").items()
    assert (fill["outcome"], fill["reason"]) == (OUTCOME_ENTRY_PENDING, HANDED_OVER.format(minutes=60))
    records = DeskRecords(PaperAccount(tmp_path, BOOK1_RULES))
    assert not records.fill_rows() and [p.trade_id for p in pending_entries(BOOK1_RULES, records)] == [trade_id]
    assert list(orders.files) == [f"{BOOK1_RULES}/orders/{trade_id}.json"] and alerts.sent == []
