"""Judge 83: C4 recomputes every owner limit itself (one seeded breach each) and checks the lot size and the monthly
expiry against NSE's own file. It also catches a sidecar rewritten to move a late capture before the cutoff."""

import json
from datetime import date

import pytest

from fno.checks.validity_account import AccountProblem
from fno.checks.validity_limits import PRICED
from fno.checks.validity_money import entry_cash_flow
from fno.quotes.recorder import QuoteSnapshotRecorder
from tests.checks.builders import committed_record
from tests.checks.validity_builders import (
    DAY,
    SHAPES,
    STARTED,
    check,
    committed_store,
    failed,
    proposal,
    proposer_max_loss,
)  # fmt: skip
from tests.checks.validity_sources import (
    FILE_DAY,
    MARGIN_ROWS,
    Margins,
    NseFiles,
    fresh_account,
    held,
    limits,
    nse_file,
)  # fmt: skip
from tests.desk.builders import CHARGES


def at_ist(hour: int, minute: int):
    return STARTED.replace(hour=hour, minute=minute)


def test_the_judges_lot_of_75_with_a_consistent_claim_is_blocked():
    claim = proposer_max_loss("SF", SHAPES["SF"][0], 200.0, lot_size=75)
    assert round(claim, 2) == 4056.23  # judge 83's number: the proposer's model, priced for 75 units
    report = check(proposal(lot_size=75, claimed_max_loss=claim))
    assert failed(report) == {"lot_size"}
    assert "NSE [65]" in next(r for r in report.failures).reason


def test_a_lot_size_nse_revised_is_blocked():
    assert failed(check(nse=NseFiles({FILE_DAY: nse_file(lot=75)}))) == {"lot_size"}


def test_the_monthly_expiry_is_nses_not_the_snapshots():
    """NSE lists 28 Oct as October's last expiry: the snapshot's 27 Oct chain is not the monthly one."""
    later = ("2026-10-20", "2026-10-27", "2026-10-28", "2026-11-24")
    assert failed(check(nse=NseFiles({FILE_DAY: nse_file(expiries=later)}))) == {"expiry"}


def test_no_nse_file_in_the_week_before_fails_closed():
    report = check(nse=NseFiles({}))
    assert failed(report) == {"listing"} and "no NSE F&O file" in report.failures[0].reason


def test_a_rewritten_sidecar_fails_with_the_quote_file_intact():
    """A capture started after the cutoff, its sidecar rewritten to 14:55 after the record was committed."""
    store = committed_store(started=at_ist(15, 5))
    record = committed_record(store, DAY, "exec")
    path = QuoteSnapshotRecorder.path(DAY, "exec.meta.json")
    meta = json.loads(store.get(path)) | {"started_at": at_ist(14, 55).isoformat()}
    store.put(path, json.dumps(meta).encode())
    report = check(store=store, record=record)
    assert failed(report) == {"evidence", *PRICED} and "meta file SHA-256" in report.failures[0].reason


def test_a_drawdown_at_the_brake_is_blocked():
    account = fresh_account(
        cash=470_000.0, closed_equity=((date(2026, 10, 1), 500_000.0), (date(2026, 10, 9), 470_000.0))
    )
    report = check(account=account)
    assert failed(report) == {"drawdown_brake"}
    assert report.failures[0].numbers["drawdown_rs"] == 30_000.0


def test_an_owner_restart_rearms_the_brake_but_never_one_that_had_not_fired():
    series = ((date(2026, 10, 1), 500_000.0), (date(2026, 10, 9), 470_000.0), (date(2026, 10, 12), 465_000.0))
    restarted = fresh_account(cash=465_000.0, closed_equity=series, restarts=(date(2026, 10, 10),))
    assert check(account=restarted).ok  # re-armed at 470,000 on 10 Oct: 5,000 below
    early = fresh_account(cash=465_000.0, closed_equity=series, restarts=(date(2026, 10, 5),))
    report = check(account=early)
    assert failed(report) == {"drawdown_brake"} and "not in force" in report.failures[0].reason


def test_a_stress_loss_over_the_limit_is_blocked():
    report = check(owner_limits=limits(max_stress_loss_rs=3_000))
    assert failed(report) == {"stress_loss"}
    assert report.failures[0].numbers["worst_loss_rs"] > 3_000


def test_an_exposure_over_the_limit_is_blocked():
    exposure = {"nifty_move_pct": 2, "max_move_loss_rs": 1_000, "iv_rise_points": 5, "max_iv_loss_rs": 15_000}
    assert failed(check(owner_limits=limits(exposure=exposure))) == {"exposure_limit"}


def test_margin_room_too_small_is_blocked():
    report = check(proposal(premium_reserved=430_000.0))
    assert failed(report) == {"margin_room"}
    assert report.failures[0].numbers["needed_rs"] == 78_050.0  # 1.45 x 9,000 + 65,000 (credit: NOV not netted)


@pytest.mark.parametrize(
    ("margins", "owner", "said"),
    [
        (Margins([]), None, "no margin row"),
        (Margins([MARGIN_ROWS[0] | {"as_of": "2026-10-01"}]), None, "too old"),
        (Margins([MARGIN_ROWS[0] | {"source": ""}]), None, "no margin row"),
        (None, "unset", "multiplier is not set"),
    ],
)
def test_a_missing_stale_or_unsourced_margin_fails_closed(margins, owner, said):
    owner_limits = limits(stressed_margin={"method": "multiplier", "multiplier": None, "source": None,
                                           "as_of": None, "max_age_days": 30}) if owner else None  # fmt: skip
    report = check(margins=margins, owner_limits=owner_limits)
    assert failed(report) == {"margin_room"} and said in report.failures[0].reason


def test_trades_chosen_earlier_the_same_day_count_in_every_limit():
    earlier = proposal("SC")
    alone, both = check(), check(proposal(earlier=(earlier,)))
    loss = {r.name: r.numbers for r in both.results}
    assert both.ok and loss["margin_room"]["needed_rs"] == 78_050.0 + 75_875.0
    worst_alone = next(r for r in alone.results if r.name == "stress_loss").numbers["worst_loss_rs"]
    assert loss["stress_loss"]["worst_loss_rs"] > worst_alone
    assert failed(check(proposal(earlier=(earlier,)), owner_limits=limits(max_open_trades=1))) == {"open_trades"}


def test_an_open_trade_without_recorded_terms_fails_the_margin():
    account = fresh_account(positions=(held("t1", {}),))
    report = check(account=account)
    assert failed(report) == {"margin_room"} and "no recorded terms" in report.failures[0].reason


def test_an_unreadable_account_fails_closed():
    class Unstarted:
        def facts(self, book, cutoff):
            raise AccountProblem("cash_ledger.csv is missing: the account has not been started")

    report = check(accounts=Unstarted())
    assert failed(report) == {"account"} and "not been started" in report.failures[0].reason


def test_an_open_trade_is_marked_and_stressed_from_the_snapshot():
    legs = {leg.contract: leg.leg.side * 65 for leg in proposal("SC").legs}
    account = fresh_account(positions=(held("t1", legs, 1_000.0),))
    report = check(proposal(open_terms={"t1": ("SC", 100.0, 1)}), account=account)
    numbers = {r.name: r.numbers for r in report.results}
    assert report.ok and set(numbers["margin_room"]["stressed_margin_rs"]) == {"t1", "c4-sf-v1:2026-10-27"}


def test_a_listing_older_than_a_week_is_not_used():
    """NSE's file 8 days before the decision day is too old: the lookback is 7 days."""
    assert failed(check(nse=NseFiles({date(2026, 10, 6): nse_file()}))) == {"listing"}
    assert check(nse=NseFiles({date(2026, 10, 7): nse_file()})).ok


def test_the_new_trades_own_liability_counts_against_an_open_debit_trade():
    """Judge 77's never-looser case: an open debit trade (worth +D) and a new credit trade (worth -P). A broker leaves
    cash + entry - P free, not more: the new trade's own liability counts."""
    bought = {leg.contract: leg.leg.side * 65 for leg in proposal("BF").legs}
    account = fresh_account(cash=494_000.0, positions=(held("t1", bought, -6_000.0),))
    report = check(proposal(open_terms={"t1": ("BF", 100.0, 1)}), account=account)
    numbers = {r.name: r.numbers for r in report.results}["margin_room"]
    sold = proposal()
    entry = entry_cash_flow([leg.leg for leg in sold.legs], 65, CHARGES)
    own = sum(leg.leg.side * 65 * leg.leg.price for leg in sold.legs)
    assert own < 0 < entry
    assert numbers["available_after_entry_rs"] == round(494_000.0 + entry + own, 2)
