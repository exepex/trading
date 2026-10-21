"""The shadow results adapter (story R1c): one shadow version's completed positions opened after its freeze day, net
after costs, oldest first; open trades, earlier positions and other versions' trades never count (judge 271)."""

from datetime import date
from types import SimpleNamespace

from fno.factory import shadow_nets
from fno.factory.shadow_nets import StrategyNets


def trade(tid, day, net, completed=True):
    return SimpleNamespace(
        trade_id=tid, opened_on=date(2026, 11, day), line=SimpleNamespace(net=net), completed=completed
    )


def test_only_this_versions_completed_positions_in_opening_order(monkeypatch):
    mine = SimpleNamespace(strategy="x1-sc-v1", positions=(trade("b", 9, -40.0), trade("a", 3, 120.0),
                                                          trade("early", 1, 5000.0)))  # fmt: skip
    other = SimpleNamespace(strategy="x2-sc-v1", positions=(trade("c", 1, 999.0),))
    seen = []

    def records(account, desk, charges):
        seen.append((account, desk, charges))
        return [mine, other]

    monkeypatch.setattr(shadow_nets, "strategy_records", records)
    nets = StrategyNets(lambda account: f"records of {account}", {"gst_pct": 18.0}).nets(
        "shadow:x1-sc-v1", date(2026, 11, 1)
    )
    assert nets == [120.0, -40.0]  # the position opened on the freeze day (1 Nov) never counts
    assert seen == [("shadow:x1-sc-v1", "records of shadow:x1-sc-v1", {"gst_pct": 18.0})]
