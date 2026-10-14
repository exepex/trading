"""Story C4: what the decision run's validator reads for itself. The versions permitted and the version's rule come
from the playbook, not from D2's outcome; the prices are the decision market's; the open trades count the trades chosen
earlier the same day."""

from dataclasses import replace
from datetime import timedelta

from fno.constants import Decision
from fno.playbook.decision_validity import validate_chosen
from fno.playbook.loader import Playbook
from fno.playbook.registry import RegistryRow
from tests.playbook.evaluation_builders import (
    DAY,
    Counts,
    FixedValues,
    OwnShadowBooks,
    chain_market,
    evaluator,
    playbook,
    strategy,
)  # fmt: skip
from tests.risk.builders import book

from .test_validity_link import validator


def chosen(*strategies):
    evaluation = evaluator().evaluate(DAY, playbook(*strategies), chain_market(), FixedValues(), book(), Counts(),
                                      OwnShadowBooks())  # fmt: skip
    return [o for o in evaluation.outcomes if o.decision == Decision.CHOSEN]


def failed(result) -> set[str]:
    return {c["check"] for c in result.record["checks"] if not c["ok"]}


def test_the_outcome_as_d2_chose_it_passes(tmp_path):
    version = strategy("sc-a")
    result = validator(tmp_path, log=False).validate(DAY, chosen(version)[0], chain_market(), playbook(version), 0)
    assert result.ok and result.reason == ""


def test_a_version_paused_before_the_day_is_not_permitted(tmp_path):
    version = strategy("sc-a")
    pause = RegistryRow("sc-a", 1, version.parameters_sha256, "paused", DAY - timedelta(days=1), "owner", "")
    paused = Playbook((version,), (*playbook(version).rows, pause))
    result = validator(tmp_path, log=False).validate(DAY, chosen(version)[0], chain_market(), paused, 0)
    assert failed(result) == {"permitted"}


def test_the_rule_is_checked_against_the_versions_own_file(tmp_path):
    version = strategy("sc-a")
    edited = strategy("sc-a", structure={**version_structure(version), "lots": 2})
    result = validator(tmp_path, log=False).validate(DAY, chosen(version)[0], chain_market(), playbook(edited), 0)
    assert failed(result) == {"version", "lots"}


def version_structure(version) -> dict:
    spec = version.structure
    expiry = {"kind": spec.expiry.kind, "min_days": spec.expiry.min_days, "max_days": spec.expiry.max_days,
              "exit_days_before_expiry": spec.expiry.exit_days_before_expiry}  # fmt: skip
    return {"code": spec.code, "strikes_rule": spec.strikes_rule, "width_rule": spec.width_rule,
            "widths": list(spec.widths), "lots": spec.lots, "expiry": expiry}  # fmt: skip


def test_the_prices_are_the_decision_markets(tmp_path):
    version = strategy("sc-a")
    outcome = chosen(version)[0]
    contract = outcome.candidate.proposal.legs[0].contract
    moved = chain_market()
    quotes = dict(moved.quotes)
    quotes[contract] = replace(quotes[contract], mid=quotes[contract].mid + 0.05)
    result = validator(tmp_path, log=False).validate(DAY, outcome, replace(moved, quotes=quotes), playbook(version), 0)
    assert any(name.startswith("leg ") for name in failed(result)) and "max_loss" in failed(result)


def test_trades_chosen_earlier_the_same_day_count_as_open(tmp_path):
    a, b = strategy("sc-a"), strategy("sc-b", expected=300.0)
    evaluation = evaluator().evaluate(DAY, playbook(a, b), chain_market(), FixedValues(), book(), Counts(),
                                      OwnShadowBooks())  # fmt: skip
    assert len(evaluation.chosen) == 2
    check = validator(tmp_path, log=False)
    check.checker.limits = replace(check.checker.limits, max_open_trades=1)
    results = validate_chosen(evaluation, check, chain_market(), playbook(a, b), book())
    assert [(key, r.ok) for key, r in results.items()] == [("sc-a-v1:2026-11-27", True), ("sc-b-v1:2026-11-27", False)]
    assert failed(results["sc-b-v1:2026-11-27"]) == {"open_trades"}


def test_the_day_checked_is_the_runs_not_the_markets(tmp_path):
    """A run on the next session reading the 13 Oct market and capture fails the date check."""
    version = strategy("sc-a")
    later = DAY + timedelta(days=1)
    result = validator(tmp_path, log=False).validate(later, chosen(version)[0], chain_market(), playbook(version), 0)
    assert "date" in failed(result)
