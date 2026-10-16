"""Story R3 criterion 8 (judge 226): a measurement version's E6 alerts and title carry `measurement`; its first
single-trade loss at or beyond the cap reads review 129's wording, a later one adds the simulator-defect escalation, and
its cumulative loss says it is expected for a measurement. Any other version keeps E6's own bytes."""

from datetime import date

from playbook.builders import document, write

from fno.books.account import PaperAccount
from fno.desk.records import DeskRecords
from fno.scorecard.pauses import ALERT, SHADOW_ONLY
from fno.scorecard.report import card_lines
from fno.scorecard.strategy_record import strategy_records

from .conftest import CHARGES, PLAN, SHADOW, START
from .history import trade

DAY, LATER = date(2026, 10, 20), date(2026, 11, 17)
E6_ALERT, E6_SHADOW = "F&O paper desk: {version} {action} ({reason})", "shadow test, not paused: the owner decides"


def measured(root, cap=10000):
    """The fixture's shadow candidate `cand-c`, rewritten as a measurement version (`edge_family: measurement`)."""
    write(root / "playbook", document(name="cand-c", evaluation_plan={**PLAN, "catastrophic_loss_rs": cap},
                                      edge_family="measurement"))  # fmt: skip


def net(root, trade_id):
    [record] = strategy_records(SHADOW, DeskRecords(PaperAccount(root, SHADOW)), CHARGES)
    return next(t.line.net for t in record.closed if t.trade_id == trade_id)


def test_e6_s_own_wording_is_unchanged_for_a_shadow_that_is_not_a_measurement(root, make_run, alerts):
    trade(root, SHADOW, "cand-c-v1", "s1", START, DAY, credit=50, debit=210)
    make_run().run(DAY, {})
    reason = f"catastrophic loss: trade s1 in {SHADOW} lost Rs {-net(root, 's1'):,.2f}, cap Rs 10,000.00"
    assert (ALERT, SHADOW_ONLY) == (E6_ALERT, E6_SHADOW)
    assert alerts.sent == [E6_ALERT.format(version="cand-c-v1", action=E6_SHADOW, reason=reason)]
    [card], _ = make_run().run(DAY, {}, account=SHADOW, pause=False)
    assert card_lines(card)[0] == f"cand-c-v1 in {SHADOW} (research)"


def test_a_measurement_s_first_loss_reads_review_129_s_wording_and_its_title_is_labelled(root, make_run, alerts):
    measured(root)
    trade(root, SHADOW, "cand-c-v1", "s1", START, DAY, credit=50, debit=210)
    [card], _ = make_run().run(DAY, {}, account=SHADOW)
    reason = f"trade s1 in {SHADOW} lost Rs {-net(root, 's1'):,.2f}, cap Rs 10,000.00"
    assert alerts.sent == [
        "F&O paper desk: cand-c-v1 (measurement) shadow test, not paused: realised loss of Rs 10,000 or more "
        f"({reason}); owner review or retirement required; no further promotion. It stays eligible for further "
        "hypothetical entries until the owner acts"
    ]
    assert card_lines(card)[0] == f"cand-c-v1 (measurement) in {SHADOW} (research)"


def test_a_measurement_s_second_loss_at_the_cap_is_escalated_as_a_possible_simulator_defect(root, make_run, alerts):
    trade(root, SHADOW, "cand-c-v1", "s1", START, DAY, credit=50, debit=210)
    trade(root, SHADOW, "cand-c-v1", "s2", DAY, LATER, credit=50, debit=210)
    measured(root, cap=-net(root, "s2"))  # the second loss exactly at the cap: E6's `<=` counts it
    make_run().run(LATER, {})
    [text] = alerts.sent
    assert "trade s2" in text and text.endswith(
        "; loss 2 at or beyond the cap: possible simulator defect (fill or settlement path), check it before any "
        "strategy relies on that path"
    )


def test_a_measurement_s_cumulative_loss_says_it_is_expected_and_repeats_on_each_close_day(root, make_run, alerts):
    measured(root)
    for n in range(5):  # 5 x about -6,600: past 3 x cap, each below the cap
        trade(root, SHADOW, "cand-c-v1", f"c{n}", START, DAY, credit=50, debit=150)
    make_run().run(DAY, {})
    total = -sum(net(root, f"c{n}") for n in range(5))
    assert alerts.sent == [
        f"F&O paper desk: cand-c-v1 (measurement) shadow test, not paused: cumulative loss: realised Rs {total:,.2f}, "
        "3 x cap Rs 10,000.00; expected for a measurement (no edge), not a defect; the owner decides"
    ]
    trade(root, SHADOW, "cand-c-v1", "c5", DAY, LATER, credit=50, debit=60)  # a small loss on a later close day
    make_run().run(LATER, {})
    assert len(alerts.sent) == 2 and "expected for a measurement" in alerts.sent[1]


def test_a_day_with_both_alerts_sends_the_single_trade_wording(root, make_run, alerts):
    measured(root)
    for n in range(3):
        trade(root, SHADOW, "cand-c-v1", f"c{n}", START, DAY, credit=50, debit=150)
    trade(root, SHADOW, "cand-c-v1", "big", START, DAY, credit=50, debit=210)  # past the cap and past 3 x cap
    make_run().run(DAY, {})
    [text] = alerts.sent
    assert "realised loss of Rs 10,000 or more (trade big" in text and "cumulative" not in text


def test_two_cap_losses_closing_the_same_day_keep_the_escalation(root, make_run, alerts):
    """Self-review finding: E6 sends one alert per version a day, so the count is by close day, not by position."""
    measured(root)
    trade(root, SHADOW, "cand-c-v1", "s1", START, DAY, credit=50, debit=210)
    trade(root, SHADOW, "cand-c-v1", "s2", START, DAY, credit=50, debit=210)
    make_run().run(DAY, {})
    [text] = alerts.sent
    assert "loss 2 at or beyond the cap: possible simulator defect" in text


def test_a_measurement_approved_to_paper_is_paused_with_e6_s_own_wording(root, make_run, alerts):
    """Self-review finding: the measurement wording ("not paused") is for a research shadow only; were the owner ever
    to approve a measurement, its pause must be reported as a pause."""
    from fno.constants import BOOK1_RULES, PlaybookStatus

    from .conftest import version

    version(root / "playbook", "meas-p", PlaybookStatus.PAPER, edge_family="measurement")
    trade(root, BOOK1_RULES, "meas-p-v1", "b1", START, DAY, credit=50, debit=210)
    make_run().run(DAY, {})
    [text] = alerts.sent
    assert (
        text.startswith("F&O paper desk: meas-p-v1 paused in every book (catastrophic loss: ")
        and "measurement" not in text
    )
