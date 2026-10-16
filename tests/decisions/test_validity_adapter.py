"""Story C4: what the decision run's validator reads for itself. The versions permitted and the version's rule come
from the playbook, not from D2's outcome; the prices are the decision market's; the open trades count the trades chosen
earlier the same day."""

from dataclasses import replace
from datetime import timedelta

from fno.constants import Decision
from fno.playbook.decision_validity import validate_chosen
from fno.playbook.loader import Playbook
from fno.playbook.registry import RegistryRow
from tests.checks.validity_sources import limits
from tests.playbook.evaluation_builders import (
    DAY,
    Counts,
    FixedValues,
    OwnShadowBooks,
    book_with_open,
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
    result = validator(tmp_path, log=False).validate(
        DAY, chosen(version)[0], chain_market(), playbook(version), book(), ()
    )
    assert result.ok and result.reason == ""


def test_a_version_paused_before_the_day_is_not_permitted(tmp_path):
    version = strategy("sc-a")
    pause = RegistryRow("sc-a", 1, version.parameters_sha256, "paused", DAY - timedelta(days=1), "owner", "")
    paused = Playbook((version,), (*playbook(version).rows, pause))
    result = validator(tmp_path, log=False).validate(DAY, chosen(version)[0], chain_market(), paused, book(), ())
    assert failed(result) == {"permitted"}


def test_the_rule_is_checked_against_the_versions_own_file(tmp_path):
    version = strategy("sc-a")
    edited = strategy("sc-a", structure={**version_structure(version), "lots": 2})
    result = validator(tmp_path, log=False).validate(
        DAY, chosen(version)[0], chain_market(), playbook(edited), book(), ()
    )
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
    result = validator(tmp_path, log=False).validate(
        DAY, outcome, replace(moved, quotes=quotes), playbook(version), book(), ()
    )
    assert any(name.startswith("leg ") for name in failed(result)) and "max_loss" in failed(result)


def test_trades_chosen_earlier_the_same_day_count_as_open(tmp_path):
    a, b = strategy("sc-a"), strategy("sc-b", expected=300.0)
    evaluation = evaluator().evaluate(DAY, playbook(a, b), chain_market(), FixedValues(), book(), Counts(),
                                      OwnShadowBooks())  # fmt: skip
    assert len(evaluation.chosen) == 2
    check = validator(tmp_path, log=False, owner_limits=limits(max_open_trades=1))
    results = validate_chosen(evaluation, check, chain_market(), playbook(a, b), book())
    assert [(key, r.ok) for key, r in results.items()] == [("sc-a-v1:2026-11-27", True), ("sc-b-v1:2026-11-27", False)]
    assert failed(results["sc-b-v1:2026-11-27"]) == {"open_trades"}


def test_the_day_checked_is_the_runs_not_the_markets(tmp_path):
    """A run on the next session reading the 13 Oct market and capture fails the date check."""
    version = strategy("sc-a")
    later = DAY + timedelta(days=1)
    result = validator(tmp_path, log=False).validate(
        later, chosen(version)[0], chain_market(), playbook(version), book(), ()
    )
    assert "date" in failed(result)


def test_d2_s_eligible_versions_are_those_that_fired_and_c4_receives_them_judge_260(tmp_path):
    """Story D4 criterion 9: both versions are approved, but B's threshold is unmet, so only A is eligible; the
    validator is handed D2's set, never the approved list."""
    a = strategy("sc-a")
    b = strategy("sc-b", entry_conditions=[{"feature": "F1_atm_iv_minus_rv20", "operator": ">", "threshold": 5}])
    evaluation = evaluator().evaluate(DAY, playbook(a, b), chain_market(), FixedValues(), book(), Counts(),
                                      OwnShadowBooks())  # fmt: skip
    assert {o.opportunity.strategy.name: o.reason for o in evaluation.outcomes}["sc-b"] == "rule did not fire"
    assert evaluation.eligible == {a.key}

    class Seen:
        def validate(self, day, outcome, market, playbook, book, earlier, eligible):
            self.eligible = eligible
            return validator(tmp_path, log=False).validate(day, outcome, market, playbook, book, earlier, eligible)

    seen = Seen()
    validate_chosen(evaluation, seen, chain_market(), playbook(a, b), book())
    assert seen.eligible == {a.key}


def test_a_version_its_own_unproven_limit_refused_is_not_eligible_judge_260_addendum_1(tmp_path):
    """B is unproven (3 completed) with one open trade, so D2 refuses B by B's own limit, not for losing to A; nothing
    after D2 re-checks that limit, so Book 2 may not choose B."""

    class PerVersion(Counts):
        def completed(self, name, version):
            return 3 if name == "sc-b" else 25

        def open(self, name, version):
            return 1 if name == "sc-b" else 0

    a, b = strategy("sc-a"), strategy("sc-b", expected=300.0)
    evaluation = evaluator().evaluate(DAY, playbook(a, b), chain_market(), FixedValues(), book(), PerVersion(),
                                      OwnShadowBooks())  # fmt: skip
    reasons = {o.opportunity.strategy.name: (o.decision, o.reason) for o in evaluation.outcomes}
    assert reasons["sc-b"][0] == Decision.NOT_CHOSEN and reasons["sc-b"][1].startswith("unproven")
    assert evaluation.eligible == {a.key}


def test_a_version_that_lost_its_slot_to_another_at_c2_stays_eligible():
    """Losing the book's last slot to A is not B's own refusal: had the decider picked B, the slot was B's (C2 then
    checks B's own verdicts, and C4 checks them again)."""
    a, b = strategy("sc-a"), strategy("sc-b", expected=300.0)
    evaluation = evaluator().evaluate(DAY, playbook(a, b), chain_market(), FixedValues(), book_with_open(2), Counts(),
                                      OwnShadowBooks())  # fmt: skip
    assert [o.reason.split(":")[0] for o in evaluation.outcomes if o.decision == Decision.NOT_CHOSEN] == ["slot"]
    assert evaluation.eligible == {a.key, b.key}
