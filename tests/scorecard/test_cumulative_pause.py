"""The owner's cumulative rule (14 Oct 2026; protocol `catastrophic_loss_strategy`): a version whose realised C1 net
reaches minus 3 x its `catastrophic_loss_rs` is paused at once in every book, though each loss is below the per-trade
cap. Only the trades the per-trade rule counts count: book trades closed since the version's latest approval, every
book together. A shadow is alerted, never paused, on a day one of its trades closes."""

from datetime import date, timedelta

from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, PlaybookStatus
from fno.desk.records import DeskRecords
from fno.scorecard.strategy_record import strategy_records

from .conftest import CHARGES, PLAN, SHADOW, START, loader, version
from .history import trade

DAY = date(2026, 10, 20)


def statuses(root):
    return {s.name: str(s.status) for s in loader(root).load().strategies}


def losses(root, strategy, count, book=BOOK1_RULES, closed=DAY, opened=START):
    """`count` trades each losing Rs 6,500 plus charges (credit 50, debit 150 a unit, 65 units)."""
    for n in range(count):
        trade(root, book, strategy, f"{strategy}-{book}-{closed}-{n}", opened, closed, credit=50, debit=150)


def total(root, strategy, books=(BOOK1_RULES, BOOK2_HYBRID)):
    found = [r for b in books for r in strategy_records(b, DeskRecords(PaperAccount(root, b)), CHARGES)]
    return sum(t.line.net for r in found if r.strategy == strategy for t in r.closed)


def test_losses_each_below_the_cap_pause_the_version_at_three_caps_across_books(root, make_run, alerts):
    losses(root, "fly-a-v1", 3)
    losses(root, "fly-a-v1", 2, book=BOOK2_HYBRID)  # 5 x about -6,600: past -30,000 together
    losses(root, "fly-b-v1", 4)  # 4 x about -6,600: not yet
    _, actions = make_run().run(DAY, {})
    assert statuses(root) == {"cand-c": "research", "fly-a": "paused", "fly-b": "paper"}
    assert (
        len(actions) == 1 and "cumulative loss" in alerts.sent[0] and "fly-a-v1 paused in every book" in alerts.sent[0]
    )
    make_run().run(DAY, {})
    assert len(alerts.sent) == 1  # a rerun pauses nothing twice


def test_exactly_three_caps_pauses_and_a_paisa_less_does_not(root, make_run):
    for name, extra in (("edge-a", 0.0), ("edge-b", 0.01)):
        losses(root, f"{name}-v1", 4)
        loss = -total(root, f"{name}-v1", (BOOK1_RULES,))
        cap = loss / 3 + extra
        assert extra or 3 * cap == loss  # the boundary itself, exactly representable
        version(root / "playbook", name, PlaybookStatus.PAPER, plan={**PLAN, "catastrophic_loss_rs": cap})
    make_run().run(DAY, {})
    assert statuses(root)["edge-a"] == "paused" and statuses(root)["edge-b"] == "paper"


def test_an_approved_version_s_shadow_trades_never_count(root, make_run):
    """Judge 73's rule for the per-trade cap holds here too: only book trades count for an approved version."""
    losses(root, "fly-a-v1", 3)
    losses(root, "fly-a-v1", 3, book=SHADOW)  # with these, -39,600; book trades alone about -19,800
    make_run().run(DAY, {})
    assert statuses(root)["fly-a"] == "paper"


def test_losses_closed_before_the_latest_approval_do_not_count(root, make_run):
    before = START - timedelta(days=1)
    losses(root, "fly-a-v1", 3, opened=before - timedelta(days=3), closed=before)
    losses(root, "fly-a-v1", 2)  # only these two count: about -13,200
    make_run().run(DAY, {})
    assert statuses(root)["fly-a"] == "paper"


def test_a_shadow_past_three_caps_is_alerted_on_a_closing_day_and_never_paused(root, make_run, alerts):
    losses(root, "cand-c-v1", 5, book=SHADOW)
    make_run().run(DAY + timedelta(days=1), {})  # no shadow trade closed that day
    assert alerts.sent == []
    _, actions = make_run().run(DAY, {})
    assert statuses(root)["cand-c"] == "research" and len(actions) == 1
    assert "cand-c-v1 shadow test, not paused" in alerts.sent[0] and "cumulative loss" in alerts.sent[0]
