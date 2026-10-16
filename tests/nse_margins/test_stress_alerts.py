"""Story A14c's fail-closed line (builder self-review, 16 Oct 2026): every way a run can stop sends exactly one
#fno-desk line and writes no row, not only the named refusals; a dropped holding is counted in the line; an owner's
approval is named only on a real fall; and the 0.05 rounding absorbs the bisection's 1e-9."""

from datetime import date, timedelta

import pytest

from fno.nse_margins.stress_log import rounded_up
from fno.research_data.calendar import CalendarError
from fno.storage.owner_token import DriveSignInRefused

from .span_builder import EXPIRY, default_options, span_zip
from .stress_days import EXPIRY2, measured_tracker, planted, weekday
from .test_stress_run import SPIKE, THROUGH, run


def consent_expired(day):
    raise DriveSignInRefused("Drive answered invalid_grant")


def calendar_ends(day):
    if day > date(2026, 11, 20):  # an exit in a year the calendar has no rows for (NSE's next circular not added)
        raise CalendarError(f"{day}: outside the session calendar")
    return weekday(day)


@pytest.mark.parametrize(("read", "trading", "said"), [
    (consent_expired, None, "unexpected DriveSignInRefused: Google refused the Drive upload sign-in"),
    (None, calendar_ends, "unexpected CalendarError"),
], ids=["Drive consent expired", "calendar year missing"])  # fmt: skip
def test_an_unexpected_stop_sends_one_line_and_writes_no_row(tmp_path, read, trading, said):
    files = planted(THROUGH)

    def tracker():
        held = measured_tracker()
        held.is_trading_day = trading or weekday  # the exit rule asks the calendar
        return held

    code, row, sent = run(tmp_path, files, workers=4, read=read, is_trading_day=trading or weekday, tracker=tracker)
    assert code == 1 and row[0] == "2026-10-14" and len(sent) == 1
    assert "nothing written: stopped by an" in sent[0] and said in sent[0]


def without_a_held_leg(day):
    """Day `day`'s planted file with the SF 100's 20,100 call missing (a strike no longer listed)."""
    options = default_options()
    options.pop(("C", 20100.0))
    return span_zip(
        member=f"nsccl.{day:%Y%m%d}.i1.spn",
        created=f"{day - timedelta(days=1):%Y%m%d}2128",
        futures=(date(2026, 10, 27), EXPIRY, EXPIRY2),
        series={EXPIRY: options, EXPIRY2: options},
    )


def test_a_dropped_holding_is_counted_in_the_line(tmp_path):
    gone = date(2026, 10, 9)
    files = planted(THROUGH, {SPIKE: 20.0}) | {gone: without_a_held_leg(gone)}
    code, row, sent = run(tmp_path, files)
    assert code == 0 and row[1:5] == ["1.7", "1.7", "1.686747", "applied"]  # the spike before the hole still counts
    assert "holding(s) dropped, not entered or skipped for an impossible price (named in the evidence)" in sent[0]
    evidence = (tmp_path / "evidence" / "stress_evidence_2026-11-05.md").read_text(encoding="utf-8")
    assert "SF 100 entered 2026-10-01: " in evidence


def test_an_approval_is_named_only_on_a_real_fall(tmp_path):
    _, rise, sent = run(tmp_path / "rise", planted(THROUGH, {SPIKE: 20.0}), approved="da0f769d")
    assert rise[4] == "applied" and "needed 1.6867; fall approved" not in sent[0]  # credit rose: no approval named
    debit_fell = "BF 100 entered 2026-10-01 peak 2026-10-01 needed 1.0000; fall approved by the owner"
    assert debit_fell in sent[0]
    _, fall, sent = run(tmp_path / "fall", planted(THROUGH, {SPIKE: 8.0}), approved="da0f769d")
    assert fall[1] == "1.3" and "needed 1.2530; fall approved by the owner, DESK_DECISIONS da0f769d" in sent[0]


@pytest.mark.parametrize(("value", "factor"), [(1.40 + 1e-9, 1.40), (1.400001, 1.45), (1.40, 1.40), (1.7483, 1.75)])
def test_rounding_absorbs_the_bisection_s_upper_end(value, factor):
    assert rounded_up(value) == factor
