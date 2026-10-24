"""Story T1e criterion 10 (judge 577 finding 1): every reason code the card can give is in the pinned dashboard
contract's `reason` list, since the delivery's `reason_code` is the dashboard card's `reason`. Both lists are read,
never typed here: the card's own code tables and the pinned `fno-card.yaml`. Red until the contract change (W3i) is
re-pinned, so T1e cannot go live before the dashboard can show its code."""

import yaml

from fno.cards import ruled_status, status
from fno.market_read_models.wiring import CONTRACT_FOLDER

CARD_SCHEMA = CONTRACT_FOLDER / "api" / "schemas" / "fno-card.yaml"


def card_codes() -> set[str]:
    """T1's reasons (the registry reading) and T2/T1e's severity order: every code a card can carry."""
    return set(status.REASONS) | set(ruled_status.SEVERITY)


def pinned_reasons() -> set:
    return set(yaml.safe_load(CARD_SCHEMA.read_text(encoding="utf-8"))["FnoCard"]["properties"]["reason"]["enum"])


def missing_from(reasons: set) -> list[str]:
    return sorted(card_codes() - reasons)


def test_every_reason_the_card_can_give_is_in_the_pinned_contract():
    assert not missing_from(pinned_reasons()), (
        f"card reason codes not in the pinned contract: {missing_from(pinned_reasons())}"
    )


def test_a_contract_without_a_card_code_names_that_code():
    reasons = card_codes() - {"step_problems"}
    assert missing_from(reasons) == ["step_problems"] and missing_from(card_codes()) == []
    assert {"step_problems", "hard_rule_breach", "trade_fields_not_built"} <= card_codes()
