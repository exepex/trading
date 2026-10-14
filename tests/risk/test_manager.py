"""Story C2 end to end: the risk manager as the app wires it (config.yaml `risk`, B2's cost model), its decision record,
and failing closed on unusable inputs."""

from datetime import date, timedelta

import pytest

from fno.config import load_app_config
from fno.risk.manager import RiskManager
from fno.risk.margins import MARGIN_COLUMNS
from fno.risk.verdict import RiskRule
from fno.risk.wiring import build_risk_manager

from .builders import DAY, FLY, book, market, open_trade, proposal, short_fly

EXPIRY = DAY + timedelta(days=14)
PRICES = {(25000, "CE"): 150.0, (25000, "PE"): 140.0, (25200, "CE"): 70.0, (24800, "PE"): 60.0}
RULES = [
    "inputs",
    "max_loss_per_trade",
    "max_open_trades",
    "drawdown_brake",
    "stress_loss",
    "exposure_limit",
    "margin_room",
]


def _manager(tmp_path, **risk) -> RiskManager:
    margins = tmp_path / "margins.csv"
    margins.write_text(",".join(MARGIN_COLUMNS) + "\nSF,200,40000,0,0,test calculator,2026-10-12\n")
    stressed = {"multiplier": 1.5, "source": "test factor", "as_of": "2026-10-13"}
    overrides = {"risk": {"margins": {"file": str(margins)}, "stressed_margin": stressed, **risk}}
    return build_risk_manager(load_app_config(overrides=overrides), tmp_path)


def _evaluate(manager, lots=1, the_book=None):
    new = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY, lots=lots)
    return manager.evaluate(new, the_book or book(), market(25000, PRICES, EXPIRY))


def test_inside_every_limit_the_trade_may_open_and_every_rule_reports(tmp_path):
    decision = _evaluate(_manager(tmp_path))
    assert decision.ok, decision.reasons
    assert [v.rule for v in decision.verdicts] == RULES
    record = decision.record()
    assert record["stressed_margin"] == {
        "method": "multiplier",
        "stresses": "scan risk only (judge 75)",
        "multiplier": "1.5",
        "source": "test factor",
        "as_of": "2026-10-13",
    }
    assert record["day"] == "2026-10-13" and record["book"] == "book1_rules"


def test_outside_the_per_trade_limit_the_trade_is_refused_with_reason_and_numbers(tmp_path):
    decision = _evaluate(_manager(tmp_path), lots=4)
    assert not decision.ok
    loss = next(v for v in decision.verdicts if v.rule == "max_loss_per_trade")
    assert not loss.ok and loss.numbers["max_loss_rs"] > 10000 and "above the limit Rs 10,000.00" in loss.reason


def test_borderline_the_limit_equal_to_the_maximum_loss_passes_and_a_paisa_less_refuses(tmp_path):
    loss = _evaluate(_manager(tmp_path)).verdicts[1].numbers["max_loss_rs"]
    assert _evaluate(_manager(tmp_path, max_loss_per_trade_rs=loss)).verdicts[1].ok
    assert not _evaluate(_manager(tmp_path, max_loss_per_trade_rs=loss - 0.01)).verdicts[1].ok


def test_the_repository_settings_refuse_every_trade_until_margin_rows_are_entered():
    decision = _evaluate(build_risk_manager(load_app_config()))
    margin = next(v for v in decision.verdicts if v.rule == "margin_room")
    assert not decision.ok and not margin.ok and "input not usable" in margin.reason


def _repository_factor_on(tmp_path, day):
    """The repository's own stressed-margin settings (owner, 14 Oct 2026: 1.45, as_of 14 Oct, 30 days), with a fresh
    margin row for `day` (A14's job writes these daily)."""
    margins = tmp_path / "margins.csv"
    margins.write_text(",".join(MARGIN_COLUMNS) + f"\nSF,200,40000,0,0,test calculator,{day}\n")
    manager = build_risk_manager(load_app_config(overrides={"risk": {"margins": {"file": str(margins)}}}), tmp_path)
    new = proposal("new", FLY, 200, short_fly(25000, 200), day + timedelta(days=14))
    decision = manager.evaluate(new, book(), market(25000, PRICES, day + timedelta(days=14), day=day))
    return decision, next(v for v in decision.verdicts if v.rule == "margin_room")


@pytest.mark.parametrize("day", [date(2026, 10, 14), date(2026, 11, 13)])
def test_the_owner_s_factor_lets_a_valid_trade_open_through_its_30th_day(tmp_path, day):
    decision, margin = _repository_factor_on(tmp_path, day)
    assert decision.ok, decision.reasons
    assert margin.numbers["multiplier"] == "1.45" and margin.numbers["as_of"] == "2026-10-14"


def test_from_the_31st_day_every_trade_is_refused_until_the_factor_is_renewed(tmp_path):
    decision, margin = _repository_factor_on(tmp_path, date(2026, 11, 14))
    assert not decision.ok and "stressed margin multiplier of 2026-10-14 is not valid on 2026-11-14" in margin.reason


def test_a_missing_quote_fails_closed_in_every_rule_that_needs_it(tmp_path):
    held = open_trade("held", FLY, 200, short_fly(24000, 200), EXPIRY, 0.0)  # no quotes for its contracts
    decision = _evaluate(_manager(tmp_path), the_book=book([held]))
    refused = {v.rule for v in decision.verdicts if not v.ok}
    assert {"stress_loss", "exposure_limit"} <= refused and not decision.ok  # margin room needs no quote of it
    assert all("no quote" in v.reason for v in decision.verdicts if v.rule == "stress_loss")


def test_a_stale_mark_cannot_price_a_new_trade(tmp_path):
    new = proposal("new", FLY, 200, short_fly(25000, 200), EXPIRY)
    stale = market(25000, PRICES, EXPIRY, stale=frozenset({(25000, "CE")}))
    decision = _manager(tmp_path).evaluate(new, book(), stale)
    assert not decision.ok and "stale" in decision.verdicts[1].reason


def test_a_proposal_reusing_an_open_trade_id_is_refused(tmp_path):
    held = open_trade("new", FLY, 200, short_fly(25000, 200), EXPIRY, 0.0)
    assert not _evaluate(_manager(tmp_path), the_book=book([held])).verdicts[0].ok


def test_a_bug_in_a_rule_is_not_swallowed():
    class Broken(RiskRule):
        name = "broken"

        def check(self, proposal, book, market):
            raise KeyError("bug")

    with pytest.raises(KeyError):
        _evaluate(RiskManager([Broken()], {}))
