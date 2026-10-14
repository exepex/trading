"""Story C3: each data check on fake snapshots and packs. Criterion 1: a snapshot outside its window, or whose hash
differs from the pack, means "no new trade: stale or unverified data" with an alert. Criterion 2: a trade needing a leg
without a valid A4 quote is not opened, before any leg is priced. Spot within 2% of the previous close unless a shock is
flagged; the previous session's NSE file present (A7 calendar)."""

from datetime import date

import pytest

from fno.checks.shock import NO_SOURCE, ShockFlags
from fno.constants import DATA_UNVERIFIED, OPTION_CALL, OPTION_PUT, OUTCOME_REFUSED
from tests.desk.builders import DAY, EXPIRY, at, enter, fly_order, fly_rows, write_snapshot

from .builders import CALENDAR, ExecutionWindow, gate, nse_files, pack_of

CE, PE = OPTION_CALL, OPTION_PUT
LEGS = tuple(fly_order().contracts())


def checked(store, snapshots, alerts, rows=None, started=(15, 15), finished=(15, 15, 40), **pack):
    write_snapshot(store, "exec", rows or fly_rows(), at(*started), at(*finished))
    gate_kwargs = {k: pack.pop(k) for k in ("schedule", "shocks", "nse") if k in pack}
    return gate(snapshots, alerts, DAY, **gate_kwargs).check(pack_of(store, DAY, **pack), LEGS)


def test_good_data_passes_and_sends_no_alert(store, snapshots, alerts):
    snapshot, report = checked(store, snapshots, alerts)
    assert report.ok and snapshot.snapshot_id == "exec" and alerts.sent == []
    assert report.legs == LEGS and (report.day, report.snapshot_id) == (DAY, "exec")


@pytest.mark.parametrize(("started", "finished"), [((14, 30), (14, 30, 40)), ((15, 9, 50), (15, 10, 30)),
                                                   ((15, 19), (15, 20, 1))])  # fmt: skip
def test_a_snapshot_outside_its_window_is_stale(store, snapshots, alerts, started, finished):
    _, report = checked(store, snapshots, alerts, started=started, finished=finished)
    assert not report.ok and report.prices_unverified
    assert "outside its window 15:10:00-15:20:00" in report.reason() and report.reason().startswith(DATA_UNVERIFIED)
    assert len(alerts.sent) == 1 and DATA_UNVERIFIED in alerts.sent[0]


def test_a_snapshot_exactly_at_its_window_edges_passes(store, snapshots, alerts):
    assert checked(store, snapshots, alerts, started=(15, 10), finished=(15, 20))[1].ok


def test_a_hash_differing_from_the_pack_or_a_snapshot_the_pack_does_not_record_fails(store, snapshots, alerts):
    _, report = checked(store, snapshots, alerts, sha="0" * 64)
    assert "differs from the pack's 0000" in report.reason() and report.prices_unverified
    _, report = checked(store, snapshots, alerts, named="other")
    assert "does not record snapshot exec" in report.reason()


def test_an_unreadable_or_unnamed_snapshot_fails(store, snapshots, alerts):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40), sha="f" * 64)  # file and sidecar disagree
    pack = pack_of(store, DAY, sha="f" * 64)
    snapshot, report = gate(snapshots, alerts, DAY).check(pack, LEGS)
    assert snapshot is None and "does not match its meta" in report.reason() and report.prices_unverified

    class Nothing(ExecutionWindow):
        def capture(self, pack):
            return None

    _, report = gate(snapshots, alerts, DAY, schedule=Nothing()).check(pack, LEGS)
    assert f"no execution capture is named for {DAY}" in report.reason()


class Flagged(ShockFlags):
    source = "the owner's shock file (test)"

    def flagged(self, day):
        return "owner: budget day gap"


@pytest.mark.parametrize(("spot", "ok"), [(24_900 * 1.02, True), (24_900 * 0.98, True), (24_900 * 1.0201, False),
                                          (24_900 * 0.9799, False)])  # fmt: skip
def test_spot_must_be_within_2_percent_of_the_previous_close(store, snapshots, alerts, spot, ok):
    _, report = checked(store, snapshots, alerts, spots=(spot,))
    assert report.ok is ok
    if not ok:
        assert "beyond 2%" in report.reason() and NO_SOURCE in report.reason() and report.prices_unverified


def test_a_flagged_shock_allows_a_larger_move(store, snapshots, alerts):
    assert checked(store, snapshots, alerts, spots=(26_000.0,), shocks=Flagged())[1].ok


def test_spot_without_a_previous_close_or_with_two_values_fails(store, snapshots, alerts):
    assert "no official close of the previous session 2026-10-13" in checked(
        store, snapshots, alerts, close=None)[1].reason()  # fmt: skip
    assert "2 different spot values" in checked(store, snapshots, alerts, spots=(25_000.0, 25_010.0))[1].reason()


def test_the_previous_session_s_nse_file_must_be_present_by_the_a7_calendar(store, snapshots, alerts):
    _, report = checked(store, snapshots, alerts, nse=nse_files(date(2026, 10, 12)))  # not the previous session
    assert "previous session 2026-10-13 is not archived" in report.reason()
    assert not report.prices_unverified  # new trades stop; exits still run at valid quotes
    assert CALENDAR.previous_session(date(2026, 10, 21)) == date(2026, 10, 19)  # 20 Oct is a holiday (Dussehra)


@pytest.mark.parametrize(("change", "problem"), [
    ({"bid": 0.0}, "one-sided or empty book"), ({"ask": None}, "one-sided or empty book"),
    ({"bid": 152.0}, "crossed (bid above ask)"), ({"bid_qty": 0.0}, "no size"), ({"size": 0.0}, "no size"),
    ({"valid": False, "reason": "no trade today (quote age unknown, possibly stale)"}, "no trade today"),
    (None, "no quote in the snapshot"),
])  # fmt: skip
def test_a_trade_needing_an_unusable_leg_is_refused_before_any_leg_fills(root, store, snapshots, alerts, entry_desk,
                                                                         change, problem):  # fmt: skip
    """The short 25000 CE fails A4's rule: nothing is priced, so no protective leg fills and no legging cost arises."""
    rows = fly_rows({(25000, CE): change})
    snapshot, report = checked(store, snapshots, alerts, rows=rows)
    assert not report.prices_unverified and f"{EXPIRY} 25000 CE: {problem}" in report.reason()
    result = enter(root, snapshots, entry_desk, fly_order(), checks=report)
    assert result.outcome == OUTCOME_REFUSED and result.reason.startswith(DATA_UNVERIFIED)
    assert result.legging_cost_rs is None


def test_a_valid_flag_on_a_crossed_book_is_not_trusted(store, snapshots, alerts):
    """The rule is checked from the quote's own numbers, not only the recorder's `valid` column."""
    _, report = checked(store, snapshots, alerts, rows=fly_rows({(25000, PE): {"bid": 142.0, "valid": True}}))
    assert "25000 PE: crossed (bid above ask)" in report.reason()
