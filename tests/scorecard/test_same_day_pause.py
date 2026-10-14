"""Story E6 with D2 (orchestrator, 14 Oct 2026): an automatic pause written on a day stops that version's trade the
same day through D2's evaluator, and a drifted version is never approved even before its pause row is written."""

from datetime import date, timedelta

from playbook.builders import LIVE_FEATURES, FixedReports, report

from fno.constants import BOOK1_RULES
from fno.playbook.approval_checks import LiveFeaturesValidated
from tests.playbook.evaluation_builders import SPOT, Counts, FixedValues, OwnShadowBooks, evaluator, price
from tests.risk.builders import book, market

from .conftest import START, loader
from .history import trade

DAY = date(2026, 10, 21)  # a session after the approvals (dated 14 Oct); 20 Oct is a holiday
F1_LIVE, F3_LIVE = LIVE_FEATURES


def chain(day):
    """D2's fixture chain, its monthly expiry 45 days after `day` (inside the fixture versions' entry window)."""
    prices = {(k, kind): price(k, kind) for k in range(24_000, 26_050, 50) for kind in ("CE", "PE")}
    return market(SPOT, prices, day + timedelta(days=45), day=day)


def book1_versions(playbook, day=DAY):
    """The versions D2's evaluator considers for Book 1 on `day` (shadow candidates aside)."""
    evaluation = evaluator().evaluate(day, playbook, chain(day), FixedValues(), book(), Counts(), OwnShadowBooks())
    return {o.opportunity.strategy.name for o in evaluation.outcomes if o.opportunity.mode != "shadow"}


def test_a_hard_loss_pause_written_on_the_day_stops_that_day_s_trade(root, make_run):
    assert book1_versions(loader(root).load()) == {"fly-a", "fly-b"}  # both are evaluated before the pause
    trade(root, BOOK1_RULES, "fly-a-v1", "t1", START, DAY, credit=50, debit=210)  # closed today: -Rs 10,400
    make_run().run(DAY, {})  # the scorecard run before 15:00 writes the pause row dated today
    playbook = loader(root).load()
    assert book1_versions(playbook) == {"fly-b"}
    assert [s.name for s in playbook.approved_on(DAY - timedelta(days=1))] == ["fly-a", "fly-b"]  # rebuilds unchanged


def test_a_drifted_version_is_not_approved_on_the_day_even_before_its_pause(root):
    f1_disagrees = FixedReports({F1_LIVE: report(F1_LIVE, 17), F3_LIVE: report(F3_LIVE, 20)})
    playbook = loader(root, (LiveFeaturesValidated(f1_disagrees),)).load()  # no scorecard run yet: no pause row
    assert [s.name for s in playbook.approved_on(DAY)] == ["fly-b"] and book1_versions(playbook) == {"fly-b"}
