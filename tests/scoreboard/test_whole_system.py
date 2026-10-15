"""Story S2 end to end on fixture histories of the three books, wired as the app wires them:

- criterion 1: every number design 12.5 lists is present for each book and section;
- criterion 2: each account reconciles with C1's three ledgers to the rupee;
- criterion 3: pilot (before the common start), unscored and overridden trades stay out of the head-to-head figures
  and are shown apart;
- criterion 4: a rebuild from the same records gives the same bytes.

Common start: Book 1 decides alone on 14 Oct (pilot); all three decide on time on 16 Oct, the common start."""

from datetime import date

import pytest

from fno.accounting.ledgers import trade_line
from fno.books.account import PaperAccount
from fno.books.equity import trade_positions
from fno.composition import build_session_calendar, open_account_writer
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, BOOKS
from fno.scoreboard.daily_values import key_of
from fno.scoreboard.ports import ProtocolStatus
from fno.scoreboard.sections import AI_NOT_AVAILABLE
from fno.scoreboard.whole_system import canonical, write_board
from fno.scoreboard.wiring import board_from
from tests.scorecard.history import CHARGES, LONG, SHORT, trade

from .builders import record, versions, write_log, write_run

PILOT_DAY, START, CLOSE, ON = date(2026, 10, 14), date(2026, 10, 16), date(2026, 10, 21), date(2026, 10, 23)
R1, R2, R3, R4 = f"{PILOT_DAY}-r1", f"{START}-r1", f"{START}-r1", f"{START}-r1"  # each book's own store
VERSIONS = versions(*((book, f"{book}-v1", date(2026, 10, 1)) for book in BOOKS))
MARKS = {key_of(LONG): 15.0, key_of(SHORT): 50.0}
SECTION_KEYS = {
    "period", "trades", "closed_trades", "gross_rs", "pads_rs", "charges_rs", "execution_costs_rs", "closed_net_rs",
    "operating_costs_rs", "ai_cost_allocated_rs", "raw_account_net_rs", "net_rs", "risk", "uncertainty", "valuation",
}  # fmt: skip
RISK_KEYS = {"max_loss_at_entry_rs", "risk_days_rs", "mean_daily_risk_rs", "net_per_unit_of_risk", "margin_days_rs",
             "margin_days_method", "stress_reserve_days_rs", "stress_usage_at_entry_max", "no_max_loss",
             "no_capital"}  # fmt: skip


def history(tmp_path, common=True):
    """The fixture's records; without `common`, books 2 and 3 never decide, so the comparison never starts."""
    for book in BOOKS:
        with open_account_writer(book, tmp_path) as writer:
            writer.start(date(2026, 10, 13))
    trade(tmp_path, BOOK1_RULES, "fly-a-v1", "p1", PILOT_DAY, date(2026, 10, 19), credit=50, debit=30)
    trade(tmp_path, BOOK1_RULES, "fly-a-v1", "h1", START, CLOSE, credit=60, debit=20)
    trade(tmp_path, BOOK1_RULES, "fly-a-v1", "o1", START, CLOSE, credit=40, debit=45)
    trade(tmp_path, BOOK1_RULES, "fly-a-v1", "u1", START, CLOSE, credit=55, debit=50)  # no committed record
    trade(tmp_path, BOOK2_HYBRID, "env-v1", "h2", START, credit=45)  # still open on ON
    write_run(tmp_path, BOOK1_RULES, PILOT_DAY, R1, record(BOOK1_RULES, PILOT_DAY, R1, "d-p1", max_loss=8000))
    write_run(
        tmp_path,
        BOOK1_RULES,
        START,
        R2,
        record(BOOK1_RULES, START, R2, "d-h1", max_loss=6000, stress=(12_000, 30_000)),
        record(BOOK1_RULES, START, R2, "d-o1", max_loss=7000, override="owner"),
    )
    write_run(tmp_path, BOOK2_HYBRID, START, R3, record(BOOK2_HYBRID, START, R3, "d-h2", max_loss=9000))
    write_run(tmp_path, BOOK3_AI, START, R4)
    write_log(tmp_path, PILOT_DAY, {BOOK1_RULES: R1, BOOK2_HYBRID: None, BOOK3_AI: None})
    others = {BOOK2_HYBRID: R3, BOOK3_AI: R4} if common else {BOOK2_HYBRID: None, BOOK3_AI: None}
    write_log(tmp_path, START, {BOOK1_RULES: R2, **others})
    (tmp_path / "journal" / BOOK2_HYBRID / "operating_costs.csv").write_text(
        "month,item,category,amount_rs,source\n2026-10,quotes,data,500.0,fixture\n"
    )
    return tmp_path


@pytest.fixture
def root(tmp_path):
    return history(tmp_path)


def build(root):
    board = board_from(root, CHARGES, build_session_calendar(), VERSIONS, lambda day: MARKS, ProtocolStatus(1, False))
    return board.build(ON)


def net(root, book, trade_id):
    position = trade_positions(PaperAccount(root, book).fills())[trade_id]
    return trade_line(position.as_ledger_trade(), CHARGES).net


def test_pilot_unscored_and_overridden_trades_stay_out_of_the_head_to_head(root):
    board = build(root)
    one = board["books"][BOOK1_RULES]
    assert (
        board["common_start"] == START.isoformat()
        and board["protocol"] == "protocol v1, not frozen: figures provisional"
    )
    assert one["pilot"]["trades"]["ids"] == ["p1"] and one["head_to_head"]["trades"]["ids"] == ["h1"]
    assert one["pilot"]["label"] == "pilot, not counted"
    assert one["overridden"]["trades"]["ids"] == ["o1"] and one["unscored"]["trades"]["ids"] == ["u1"]
    assert list(one["head_to_head"]["segments"]) == [f"{BOOK1_RULES}/{BOOK1_RULES}-v1"]
    assert one["overall"]["trades"]["ids"] == ["p1", "h1", "o1", "u1"]


def test_head_to_head_net_and_net_per_unit_of_risk_by_hand(root):
    sessions = build_session_calendar().sessions(START, ON)
    held = sum(START <= day < CLOSE for day in sessions)  # held at the close from entry to the day before the exit
    h2h = build(root)["books"][BOOK1_RULES]["head_to_head"]
    assert h2h["closed_net_rs"] == round(net(root, BOOK1_RULES, "h1"), 2) == h2h["raw_account_net_rs"]
    assert h2h["risk"]["risk_days_rs"] == 6000 * held
    assert h2h["risk"]["net_per_unit_of_risk"] == round(net(root, BOOK1_RULES, "h1") / (6000 * held), 6)
    assert h2h["risk"]["stress_usage_at_entry_max"] == 0.4 and h2h["risk"]["margin_days_rs"] == 9000 * held
    assert h2h["risk"]["stress_reserve_days_rs"] == 0.0  # STR1b: the reserve is apart, never in the capital figure
    assert h2h["uncertainty"]["sample_met"] is False and h2h["ai_cost_allocated_rs"] == 0.0
    assert h2h["uncertainty"]["figures"] == "S1 proposal, provisional: not decided by the owner"


def test_an_open_trade_is_marked_and_operating_costs_and_unknown_ai_cost_are_stated(root):
    two = build(root)["books"][BOOK2_HYBRID]["head_to_head"]
    cash = sum(f.amount for f in PaperAccount(root, BOOK2_HYBRID).fills())
    marked = cash + 65 * MARKS[key_of(LONG)] - 65 * MARKS[key_of(SHORT)]
    assert two["raw_account_net_rs"] == round(marked - 500.0, 2) and two["operating_costs_rs"] == 500.0
    assert two["ai_cost_allocated_rs"] == AI_NOT_AVAILABLE and two["net_rs"] is None
    assert two["trades"]["open"] == 1 and two["closed_trades"] == 0


def test_every_listed_number_is_present_for_each_book_and_section(root):
    board = build(root)
    for book in BOOKS:
        for name in ("overall", "pilot", "head_to_head", "unscored", "overridden"):
            assert set(board["books"][book][name]) >= SECTION_KEYS, (book, name)
            assert set(board["books"][book][name]["risk"]) == RISK_KEYS


def test_every_account_reconciles_with_the_three_ledgers(root):
    board = build(root)
    for book in BOOKS:
        assert board["books"][book]["reconciliation"]["ok"], book
    one = board["books"][BOOK1_RULES]["reconciliation"]
    assert one["account_closed_net_rs"] == round(sum(net(root, BOOK1_RULES, t) for t in ("p1", "h1", "o1", "u1")), 2)


def test_a_rebuild_from_the_same_records_gives_the_same_bytes(root):
    first = write_board(root, build(root)).read_bytes()
    assert write_board(root, build(root)).read_bytes() == first == canonical(build(root)).encode("utf-8")
    assert "journal/runs/2026-10-16.json" in build(root)["inputs_sha256"]


def test_a_trade_ledger_that_differs_from_the_account_does_not_reconcile(root):
    """C1 recomputes each trade from its fills with today's charges table: a table that changed since the fills were
    charged gives a different trade ledger, and the board says so instead of hiding it."""
    changed = {**CHARGES, "brokerage_per_order": CHARGES["brokerage_per_order"] + 10}
    board = board_from(root, changed, build_session_calendar(), VERSIONS, lambda day: MARKS, ProtocolStatus(1, False))
    one = board.build(ON)["books"][BOOK1_RULES]["reconciliation"]
    assert one["ok"] is False and one["checks"]["trade_ledger"] is False and one["checks"]["cash_ledger"] is True


def test_a_trade_closed_after_the_report_day_is_still_open_on_it(root):
    board = board_from(root, CHARGES, build_session_calendar(), VERSIONS, lambda day: MARKS, ProtocolStatus(1, False))
    h2h = board.build(date(2026, 10, 19))["books"][BOOK1_RULES]["head_to_head"]
    assert h2h["trades"]["open"] == 1 and h2h["closed_trades"] == 0  # h1 closes on 21 Oct


def test_operating_costs_of_the_common_start_month_count_head_to_head_not_pilot(root):
    two = build(root)["books"][BOOK2_HYBRID]
    assert two["pilot"]["operating_costs_rs"] == 0.0 and two["head_to_head"]["operating_costs_rs"] == 500.0


def test_net_takes_the_allocated_ai_cost_off_the_raw_account_net():
    from fno.scoreboard.sections import section
    from fno.scoreboard.series import DailySeries

    series = DailySeries((ON,), (1000.0,), (0.0,))
    assert section([], series, 0.0, 150.0, None, ON, ON)["net_rs"] == 850.0


class TenRupeesADay:
    def allocated(self, book, first, last):
        return 10.0 * ((last - first).days + 1)


def test_the_allocated_ai_cost_is_charged_once_pilot_plus_head_to_head_is_overall(root):
    """Judge 87: the AI cost is the book's, over periods that never overlap; segments, unscored and overridden trades
    carry none of it."""
    from fno.scoreboard.book_board import AI_AT_BOOK_LEVEL, BookBoard, BookInputs

    board = BookBoard(build_session_calendar().sessions, TenRupeesADay()).build(
        BookInputs(BOOK1_RULES, (), (), date(2026, 10, 13), ON), START
    )
    pilot, h2h = board["pilot"]["ai_cost_allocated_rs"], board["head_to_head"]["ai_cost_allocated_rs"]
    assert pilot + h2h == board["overall"]["ai_cost_allocated_rs"] == 110.0 and pilot == 30.0
    assert board["unscored"]["ai_cost_allocated_rs"] == board["overridden"]["ai_cost_allocated_rs"] == AI_AT_BOOK_LEVEL
    [segment] = build(root)["books"][BOOK1_RULES]["head_to_head"]["segments"].values()
    assert segment["ai_cost_allocated_rs"] == AI_AT_BOOK_LEVEL and segment["net_rs"] == segment["raw_account_net_rs"]
