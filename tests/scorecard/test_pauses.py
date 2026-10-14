"""Story E6 criterion 1 and judge 67: a catastrophic loss or a live-feature drift pauses that version at once in every
book (paper -> paused by hard_loss_rule, one alert); the other versions keep trading; a shadow is only alerted."""

from dataclasses import replace
from datetime import date, timedelta

from playbook.builders import LIVE_FEATURES, FixedReports, report

from fno.books.account import PaperAccount
from fno.constants import APPROVER_HARD_LOSS_RULE, BOOK1_RULES, BOOK2_HYBRID, PlaybookStatus
from fno.desk.records import DeskRecords
from fno.playbook.approval_checks import LiveFeaturesValidated
from fno.scorecard.strategy_record import strategy_records

from .conftest import CHARGES, PLAN, SHADOW, START, loader, version
from .history import trade

DAY = date(2026, 10, 20)
F1_LIVE, F3_LIVE = LIVE_FEATURES


def statuses(root):
    return {s.name: str(s.status) for s in loader(root).load().strategies}


def test_a_catastrophic_loss_in_any_book_pauses_that_version_at_once_and_alerts(root, make_run, alerts):
    trade(root, BOOK2_HYBRID, "fly-a-v1", "t1", START, DAY, credit=50, debit=210)  # -Rs 10,400 before charges
    trade(root, BOOK1_RULES, "fly-b-v1", "t2", START, DAY, credit=50, debit=150)  # -Rs 6,500: below the cap
    _, actions = make_run().run(DAY, {})
    assert statuses(root) == {"cand-c": "research", "fly-a": "paused", "fly-b": "paper"}
    assert [s.name for s in loader(root).load().approved()] == ["fly-b"]  # no book may trade fly-a any more
    last = loader(root).registry.rows()[-1]
    assert (last.name, last.status, last.approved_by, last.changed_on) == (
        "fly-a",
        "paused",
        APPROVER_HARD_LOSS_RULE,
        DAY,
    )
    assert (
        len(alerts.sent) == 1 and "fly-a-v1 paused in every book" in alerts.sent[0] and "book2_hybrid" in alerts.sent[0]
    )
    assert len(actions) == 1
    make_run().run(DAY, {})  # a rerun pauses nothing twice and alerts nothing more
    assert len(alerts.sent) == 1 and len(loader(root).registry.rows()) == 3


def test_a_loss_exactly_at_the_cap_pauses_and_a_paisa_less_does_not(root, make_run):
    for name, extra in (("edge-a", 0.0), ("edge-b", 0.01)):
        trade(root, BOOK1_RULES, f"{name}-v1", f"{name}-t", START, DAY, credit=50, debit=210)
        [record] = [r for r in strategy_records(BOOK1_RULES, DeskRecords(PaperAccount(root, BOOK1_RULES)), CHARGES)
                    if r.strategy == f"{name}-v1"]  # fmt: skip
        cap = -record.closed[0].line.net + extra
        version(root / "playbook", name, PlaybookStatus.PAPER, plan={**PLAN, "catastrophic_loss_rs": cap})
    make_run().run(DAY, {})
    assert statuses(root)["edge-a"] == "paused" and statuses(root)["edge-b"] == "paper"


def test_a_drifting_version_is_paused_and_the_other_versions_keep_trading(root, make_run, alerts):
    f1_disagrees = FixedReports({F1_LIVE: report(F1_LIVE, 17), F3_LIVE: report(F3_LIVE, 20)})
    checks = (LiveFeaturesValidated(f1_disagrees),)
    assert [d.strategy.name for d in loader(root, checks).load().drifted] == ["fly-a"]
    _, actions = make_run(checks).run(DAY, {})
    assert statuses(root) == {"cand-c": "research", "fly-a": "paused", "fly-b": "paper"}
    assert [s.name for s in loader(root, checks).load().approved()] == ["fly-b"]  # fly-b uses F3 only: still valid
    assert len(actions) == 1 and "live feature drift" in alerts.sent[0] and F1_LIVE in alerts.sent[0]


def test_a_shadow_versions_catastrophic_loss_is_alerted_once_never_paused(root, make_run, alerts):
    trade(root, SHADOW, "cand-c-v1", "s1", START, DAY, credit=50, debit=210)
    make_run().run(DAY, {})
    assert statuses(root)["cand-c"] == "research" and len(loader(root).registry.rows()) == 2  # no row written
    assert len(alerts.sent) == 1 and "shadow test, not paused: the owner decides" in alerts.sent[0]
    make_run().run(date(2026, 10, 21), {})  # the next day: the same loss does not alert again
    assert len(alerts.sent) == 1


def test_report_only_fires_no_pause(root, make_run, alerts):
    trade(root, BOOK1_RULES, "fly-a-v1", "t1", START, DAY, credit=50, debit=210)
    _, actions = make_run().run(DAY, {}, pause=False)
    assert actions == [] and alerts.sent == [] and statuses(root)["fly-a"] == "paper"


def reapprove(root, name, day):
    """The owner's paused -> paper (a registry row and the file's status line, as D1's status change writes them)."""
    rows = loader(root).registry.rows()
    last = [r for r in rows if r.name == name][-1]
    row = replace(last, status=PlaybookStatus.PAPER, changed_on=day, approved_by="owner", evidence_commit="abcdef1")
    loader(root).registry.append(row)
    path = root / "playbook" / f"{name}-v1.yaml"
    path.write_text(path.read_text().replace("status: paused", "status: paper"))


def test_an_owner_re_approval_after_a_pause_sticks(root, make_run, alerts):
    """Judge 73: the old loss that caused the pause must not pause the version again after the owner re-approves."""
    trade(root, BOOK1_RULES, "fly-a-v1", "t1", START, DAY, credit=50, debit=210)
    make_run().run(DAY, {})
    assert statuses(root)["fly-a"] == "paused"
    reapprove(root, "fly-a", DAY + timedelta(days=1))
    make_run().run(DAY + timedelta(days=2), {})
    assert statuses(root)["fly-a"] == "paper" and len(alerts.sent) == 1
    trade(root, BOOK1_RULES, "fly-a-v1", "t2", DAY + timedelta(days=2), DAY + timedelta(days=3), credit=50, debit=210)
    make_run().run(DAY + timedelta(days=3), {})
    assert statuses(root)["fly-a"] == "paused" and len(alerts.sent) == 2  # a new loss after re-approval does pause


def test_a_shadow_loss_never_pauses_an_approved_version(root, make_run, alerts):
    """Judge 73: the version's earlier shadow test (or any shadow account) is evidence, never a book's loss."""
    trade(root, SHADOW, "fly-a-v1", "s1", START, DAY, credit=50, debit=210)
    make_run().run(DAY, {})
    assert statuses(root)["fly-a"] == "paper" and alerts.sent == []


def test_a_book_loss_closed_before_the_latest_approval_never_pauses(root, make_run, alerts):
    trade(root, BOOK1_RULES, "fly-a-v1", "t0", START - timedelta(days=3), START - timedelta(days=1), credit=50,
          debit=210)  # fmt: skip
    make_run().run(DAY, {})
    assert statuses(root)["fly-a"] == "paper" and alerts.sent == []


def test_a_book_loss_closed_on_the_approval_day_itself_pauses(root, make_run, alerts):
    """Judge 73 addendum 1: a loss closed ON the day of the latest approval counts (closed on or after it)."""
    trade(root, BOOK1_RULES, "fly-a-v1", "t1", START, START, credit=50, debit=210)  # approved, opened, lost: 14 Oct
    make_run().run(START, {})
    assert statuses(root)["fly-a"] == "paused" and len(alerts.sent) == 1
