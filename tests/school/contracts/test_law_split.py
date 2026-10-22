"""Judge 479 finding 3: one frozen split of the safety laws' refusals. Tickets relax only the account limits
(reviews 138 and 139); the daily stop and the brake bind tickets too (orchestrator, 22 Oct 2026)."""

from fno.school.constants import ACCOUNT_LIMITS, DRIVER_STOPS, TRADE_VALIDITY, RefusalReason, TicketReason


def test_the_account_limits_are_exactly_the_four_cash_and_bucket_limits():
    assert {RefusalReason.BUCKET_CAP, RefusalReason.OPEN_RISK, RefusalReason.NEW_RISK_DAY,
                              RefusalReason.MARGIN_ROOM} == ACCOUNT_LIMITS  # fmt: skip


def test_the_stops_are_the_daily_stop_and_the_brake():
    assert {RefusalReason.DAILY_STOP, RefusalReason.BRAKE} == DRIVER_STOPS


def test_the_three_groups_split_every_refusal_once():
    groups = (ACCOUNT_LIMITS, DRIVER_STOPS, TRADE_VALIDITY)
    assert set().union(*groups) == set(RefusalReason) and sum(map(len, groups)) == len(RefusalReason)


def test_protection_max_loss_quotes_prices_and_the_seal_are_never_account_limits():
    never = {RefusalReason.UNPROTECTED, RefusalReason.MAX_LOSS, RefusalReason.MISSING_QUOTE,
             RefusalReason.ONE_SIDED_QUOTE, RefusalReason.SIZE_ABOVE_DISPLAYED, RefusalReason.PROTECTION_UNSELLABLE,
             RefusalReason.IMPOSSIBLE_LEG_PRICE, RefusalReason.STALE_SEAL}  # fmt: skip
    assert never == TRADE_VALIDITY


def test_a_ticket_s_reasons_are_the_trade_limit_and_the_account_limit():
    assert {r.value for r in TicketReason} == {"trade_limit", "account_limit"}
