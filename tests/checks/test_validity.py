"""Story C4 criteria 1-3: three correct trades pass; each seeded wrong proposal fails with exactly the check that
names its fault; nobody can override a failure."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, time, timedelta

import pytest

from fno.checks.validity import HardValidityError, override
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.models import IST
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.research_engine.structures import BOUGHT
from tests.checks.builders import committed_record
from tests.checks.validity_builders import (
    CUTOFF,
    DAY,
    LOT,
    SHAPES,
    STARTED,
    WEEKLY,
    check,
    committed_store,
    failed,
    fly,
    legs_of,
    proposal,
    proposer_max_loss,
    snapshot_rows,
)  # fmt: skip
from tests.checks.validity_sources import PRICED, fresh_account, held


@pytest.mark.parametrize("code", ["SF", "SC", "BF"])
def test_a_correct_trade_of_each_structure_passes(code):
    report = check(proposal(code))
    assert report.ok and report.failures == () and report.mode == "playbook"
    loss = next(r for r in report.results if r.name == "max_loss").numbers
    assert loss["difference"] < 0.01  # the independent arithmetic equals the proposer's to the paisa


def _moved_leg(code: str, index: int, **leg_changes):
    legs = list(proposal(code).legs)
    legs[index] = replace(legs[index], leg=replace(legs[index].leg, **leg_changes))
    return tuple(legs)


def _rows_without(strike, kind):
    return [r for r in snapshot_rows() if (float(r["strike"]), r["type"], r["expiry"]) != (strike, kind, "2026-10-27")]


SEEDED = {
    # 1. stale date: the snapshot read is the previous session's
    "stale date": (lambda: check(store=committed_store(started=STARTED - timedelta(days=1))), {"date"}),
    # 2. wrong expiry: the legs are on the weekly expiry, listed but not monthly
    "weekly expiry": (lambda: check(proposal(legs=legs_of(SHAPES["SF"][0], WEEKLY), expiry=WEEKLY.isoformat())),
                      {"expiry", "leg 2026-10-20 25000 CE", "leg 2026-10-20 25000 PE", "leg 2026-10-20 25200 CE",
                       "leg 2026-10-20 24800 PE", "stress_loss", "exposure_limit"}),
    # 3. a strike not listed in the snapshot
    "strike not listed": (lambda: check(store=committed_store(_rows_without(25200.0, "CE"))),
                          {"leg 2026-10-27 25200 CE", *PRICED}),
    # 4. the price used is not the snapshot's mid (5 paise off); the loss claimed at the true mid no longer fits it
    "price mismatch": (lambda: check(proposal(legs=_moved_leg("SF", 0, price=proposal().legs[0].leg.price + 0.05))),
                       {"leg 2026-10-27 25000 CE", "max_loss"}),
    # 5. the claimed maximum loss is wrong by Rs 1
    "max loss off by Rs 1": (lambda: check(proposal(claimed_max_loss=proposal().claimed_max_loss + 1.0)),
                             {"max_loss"}),
    # 6. over the owner's Rs 10,000 per-trade limit (a 200-wide long fly), its claimed loss correct
    "loss over the limit": (lambda: check(proposal("BF", width=200.0, legs=legs_of(_wide_fly()),
                                                   claimed_max_loss=proposer_max_loss("BF", _wide_fly(), 200.0))),
                            {"loss_limit"}),
    # 7. a fourth open trade
    "open trades": (lambda: _three_open(), {"open_trades"}),
    # 8. the snapshot was changed after its record was committed
    "tampered hash": (lambda: _tampered_check(), {"evidence", *PRICED}),
    # 9. no committed record names the snapshot
    "missing snapshot": (lambda: check(record=None), {"evidence", *PRICED}),
    # 10. two lots where the version trades one
    "wrong lots": (lambda: check(proposal(lots=2, claimed_max_loss=proposer_max_loss("SF", SHAPES["SF"][0], 200, 2))),
                   {"lots"}),
    # 11. the version is not approved on the day
    "version not permitted": (lambda: check(proposal(approved=frozenset())), {"permitted"}),
    # 12. a condor's legs labelled a short fly
    "wrong structure": (lambda: check(proposal("SC", structure="SF")), {"structure", "shape", "margin_room"}),
    # 13. the rule fingerprint differs from the version's file
    "changed rule": (lambda: check(proposal(rule_sha256="0" * 64)), {"version"}),
    # 14. a C2 verdict failed
    "risk verdict": (lambda: check(proposal(risk_verdicts_ok=False)), {"risk_verdicts"}),
    # 15. a leg's quote arrived after the cutoff
    "quote after cutoff": (lambda: check(store=committed_store(snapshot_rows(CUTOFF + timedelta(seconds=1)))),
                           {f"leg 2026-10-27 {k} {t}" for k, t, _ in SHAPES["SF"][0]}),
    # 16. the snapshot started after the cutoff
    "snapshot after cutoff": (lambda: check(store=committed_store(started=datetime.combine(DAY, time(15, 1), IST))),
                              {"date"}),
    # 17. one leg on another expiry (the weekly, listed and priced at its own mid) than the opportunity's
    "a leg on another expiry": (lambda: check(proposal(legs=_weekly_wing())), {"expiry", "max_loss", "stress_loss"}),
    # 18. judge 83 addendum 1: a leg named 25,100 CE whose strike is 25,000 (E4 would hold one contract, mark another)
    "contract name mismatch": (lambda: check(proposal(legs=_misnamed())), {"leg 2026-10-27 25000 CE"}),
}  # fmt: skip


def _misnamed():
    legs = list(proposal().legs)
    legs[0] = replace(legs[0], contract="NIFTY26102725100CE")
    return tuple(legs)


def _three_open():
    """Three trades already open (flat legs, so only the count changes), each with its recorded terms."""
    positions = tuple(held(f"t{n}", {}) for n in range(3))
    terms = {f"t{n}": ("SF", 200.0, 1) for n in range(3)}
    return check(proposal(open_terms=terms), account=fresh_account(positions=positions))


def _weekly_wing():
    legs = list(proposal().legs)
    wing = legs[2]
    legs[2] = replace(wing, contract=wing.contract.replace("261027", "261020"), expiry=WEEKLY.isoformat(),
                      leg=replace(wing.leg, price=10.5))  # fmt: skip
    return tuple(legs)


def _wide_fly():
    return fly(25_000, 200, BOUGHT)


def _tampered_check():
    """The snapshot's quote file changed after its record was committed."""
    store = committed_store()
    record, path = committed_record(store, DAY, "exec"), QuoteSnapshotRecorder.path(DAY, "exec.csv")
    store.put(path, store.get(path).replace(b"199.5", b"199.6"))
    return check(store=store, record=record)


@pytest.mark.parametrize("name", sorted(SEEDED))
def test_each_seeded_wrong_proposal_fails_with_its_check(name):
    make, expected = SEEDED[name]
    report = make()
    assert not report.ok
    assert failed(report) == expected, [r.record() for r in report.failures]


def test_the_seeded_set_has_at_least_ten_wrong_proposals():
    assert len(SEEDED) >= 10 and LOT == 65


def test_a_claimed_loss_off_by_under_a_rupee_passes_by_a_rupee_fails():
    true = proposal().claimed_max_loss
    assert check(proposal(claimed_max_loss=true + 0.99)).ok
    assert failed(check(proposal(claimed_max_loss=true - 1.0))) == {"max_loss"}


@pytest.mark.parametrize("by", ["owner", "desk", "judge"])
def test_nobody_overrides_a_failure(by):
    report = check(proposal(risk_verdicts_ok=False))
    with pytest.raises(HardValidityError, match="cannot override hard validity"):
        override(report, by, "I accept the risk")
    with pytest.raises(FrozenInstanceError):
        report.results = ()
    assert override(check(), by, "nothing to override").ok


def test_book_3_fails_closed_without_a_registered_constitution():
    """Story D5: Book 3's mode refuses a trade when no constitution matches the registered D6 component."""
    report = check(proposal(book=BOOK3_AI))
    assert failed(report) == {"constitution"} and "no constitution file" in report.failures[0].reason


def test_book_2_fails_closed_without_a_trade_envelope():
    """Story D4: Book 2's mode refuses a trade whose version has no envelope file, so nothing passes unchecked."""
    report = check(proposal(book=BOOK2_HYBRID))
    assert "envelope" in failed(report) and "no trade envelope" in report.failures[-1].reason
