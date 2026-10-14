"""Story D2's composition: the app's evaluator builds from config.yaml with every C2 limit, and the live values adapter
asks each B7 live feature for the decision context it is given."""

from datetime import date

from fno.config import ROOT, load_app_config
from fno.constants import BOOKS
from fno.playbook.live_values import ComputedLiveFeatures
from fno.playbook.wiring import build_rule_evaluator
from fno.research_engine.features import DecisionContext, Feature


def test_the_app_evaluator_uses_every_owner_limit():
    evaluator = build_rule_evaluator(load_app_config())
    rules = {rule.name for rule in evaluator.allocator.risk.rules}
    assert rules == {
        "max_loss_per_trade",
        "max_open_trades",
        "drawdown_brake",
        "stress_loss",
        "exposure_limit",
        "margin_room",
    }
    assert evaluator.builder.cap == 10_000 and evaluator.builder.lot_size == 65
    assert evaluator.real.folders == tuple((ROOT / "journal" / name).resolve() for name in BOOKS)


class Echo(Feature):
    name = "F9_live_echo"

    def value(self, data, decision_day, context):
        return (data, decision_day, context.expiry)


def test_live_values_come_from_the_features_with_the_context():
    context = DecisionContext(date(2026, 11, 27), date(2026, 10, 13), date(2026, 11, 6))
    values = ComputedLiveFeatures([Echo()], "data").values(date(2026, 10, 13), context)
    assert values == {"F9_live_echo": ("data", date(2026, 10, 13), date(2026, 11, 27))}
