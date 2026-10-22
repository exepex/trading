"""Rupees shown to the owner (327 item 1): only account trades. A ticket's net is a measurement of the rule on that
road, never added to a rupee total; every report sums through here."""

from collections.abc import Iterable

from ..contracts.records import OutcomeRecord


def account_net(outcomes: Iterable[OutcomeRecord]) -> float:
    return sum(outcome.net for outcome in outcomes if not outcome.is_ticket)
