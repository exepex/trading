"""Story MS-P1d criterion 4 (the state behind law 7): the brake engages at Rs 1.2 lakh below the high, holds across
sessions whatever equity does, lifts only on a review row in `research/school/reviews/`, and never engages on a
session whose positions could not all be marked."""

from datetime import date, timedelta

import pytest

from fno.school.accounts.brake import EquityRow, brake_state, first_review_day
from fno.school.accounts.reviews import ReviewFile, ReviewFileError

from .account_builders import NEXT, Reviews, accounts, marks, opening, spread_quotes

# Sessions: 2 and 3 Nov, then from Mon 7 Dec. A brake engaged on 3 Nov waits for the monthly review on or after the
# first Saturday of December (5 Dec).
D = [date(2026, 11, 2), date(2026, 11, 3)] + [date(2026, 12, 7) + timedelta(days=n) for n in range(8)]
REVIEW = date(2026, 12, 5)
BRAKE = 120_000.0


def rows(*equities, stale=()):
    return [EquityRow(D[n], e, n not in stale) for n, e in enumerate(equities)]


def test_it_engages_at_the_limit_and_not_a_rupee_before():
    assert brake_state(rows(2_000_000, 1_880_001), (), BRAKE).engaged_on is None
    state = brake_state(rows(2_000_000, 1_880_000), (), BRAKE)
    assert state.engaged_on == D[1] and state.high == 2_000_000


def test_the_high_is_the_highest_marked_equity():
    assert brake_state(rows(2_000_000, 2_050_000, 1_930_001), (), BRAKE).engaged_on is None
    assert brake_state(rows(2_000_000, 2_050_000, 1_930_000), (), BRAKE).engaged_on == D[2]


def test_it_holds_across_sessions_after_equity_recovers():
    state = brake_state(rows(2_000_000, 1_870_000, 2_100_000, 2_200_000), (), BRAKE)
    assert state.engaged_on == D[1] and state.lifted_on is None


def test_a_review_row_lifts_it_from_the_next_session_and_restarts_the_high():
    state = brake_state(rows(2_000_000, 1_870_000, 1_860_000, 1_850_000), (REVIEW,), BRAKE)
    assert state.engaged_on is None and state.lifted_on == REVIEW and state.high == 1_860_000


def test_a_review_before_the_fall_or_without_a_brake_lifts_nothing():
    assert brake_state(rows(2_000_000, 1_870_000, 1_870_000), (D[0],), BRAKE).engaged_on == D[1]
    assert brake_state(rows(2_000_000, 1_990_000), (D[0],), BRAKE).lifted_on is None


def test_after_a_lift_the_high_restarts_at_the_next_fully_marked_row():
    state = brake_state(rows(2_000_000, 1_870_000, 3_000_000, 1_860_000, stale=(2,)), (REVIEW,), BRAKE)
    assert state.high == 1_860_000 and state.engaged_on is None, "never from the worst-case row"


@pytest.mark.parametrize(
    ("engaged", "review"),
    [(date(2026, 11, 3), date(2026, 12, 5)), (date(2026, 10, 22), date(2026, 11, 7)),
     (date(2026, 12, 31), date(2027, 1, 2)), (date(2026, 11, 7), date(2026, 12, 5))],
)  # fmt: skip
def test_the_review_is_the_first_saturday_of_the_next_month(engaged, review):
    assert first_review_day(engaged) == review and review.weekday() == 5


def test_a_row_before_the_monthly_review_is_an_error_never_a_lift():
    """Owner, 22 Oct 2026: "Pause till monthly review". Engaged on 3 Nov: a row of 4 Dec (the day before the first
    Saturday of December) is refused; one of 5 Dec lifts; a row of the engagement day itself is refused too."""
    fallen = rows(2_000_000, 1_870_000, 1_870_000)
    for early in (date(2026, 12, 4), D[1]):
        with pytest.raises(ReviewFileError, match="before the monthly review"):
            brake_state(fallen, (early,), BRAKE)
    assert brake_state(fallen, (REVIEW,), BRAKE).lifted_on == REVIEW


def test_it_engages_again_after_a_lift():
    state = brake_state(rows(2_000_000, 1_870_000, 1_870_000, 1_750_000), (REVIEW,), BRAKE)
    assert state.engaged_on == D[3] and state.lifted_on == REVIEW


def test_an_unmarked_session_never_engages_it_or_sets_the_high():
    assert brake_state(rows(2_000_000, 1_000_000, stale=(1,)), (), BRAKE).engaged_on is None
    assert brake_state(rows(2_000_000, 3_000_000, 2_000_000, stale=(1,)), (), BRAKE).high == 2_000_000


def test_the_account_view_carries_the_latch_and_the_review_lifts_it(tmp_path):
    reviews = Reviews()
    port, entry = accounts(tmp_path, reviews), opening(tmp_path, lots=100)  # 3,000 units: a big enough loss
    port.view("CS1@1", marks(), D[0])
    port.record("CS1@1", entry)
    fallen = port.view("CS1@1", marks(spread_quotes(60.0, 4.5), NEXT), NEXT)
    assert fallen.equity_high - fallen.equity >= BRAKE and fallen.brake_engaged_on == NEXT
    recovered = port.view("CS1@1", marks(spread_quotes(10.5, 4.5), D[2]), D[2])
    assert recovered.brake_engaged_on == NEXT, "held across sessions though equity recovered"
    reviews.rows["CS1@1"] = [date(2026, 12, 4)]
    with pytest.raises(ReviewFileError, match="before the monthly review"):
        port.view("CS1@1", marks(spread_quotes(10.5, 4.5), D[2]), D[2])
    reviews.rows["CS1@1"] = [D[2]]
    assert port.view("CS1@1", marks(spread_quotes(10.5, 4.5), D[2]), D[2]).brake_engaged_on == NEXT, "not yet"
    lifted = port.view("CS1@1", marks(spread_quotes(10.5, 4.5), D[3]), D[3])
    assert lifted.brake_engaged_on is None and lifted.brake_lifted_on == D[2]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return ReviewFile(path)


def test_the_review_file(tmp_path):
    reviews = ReviewFile(tmp_path / "none.csv")
    assert reviews.lifts("CS1@1", D[5]) == ()
    reviews = write(
        tmp_path / "r.csv",
        "reviewed_on,driver_id,review_ref\n2026-11-07,CS1@1,review 2026-11\n"
        "2026-11-07,DB1@1,review 2026-11\n2026-12-05,CS1@1,review 2026-12\n",
    )
    assert reviews.lifts("CS1@1", date(2026, 12, 5)) == (date(2026, 11, 7),), "a row of the session itself waits"
    assert reviews.lifts("CS1@1", date(2026, 12, 6)) == (date(2026, 11, 7), date(2026, 12, 5))


@pytest.mark.parametrize(
    ("text", "error"),
    [
        ("day,driver_id,review_ref\n", "columns"),
        ("reviewed_on,driver_id,review_ref\n7 Nov,CS1@1,r\n", "not a date"),
        ("reviewed_on,driver_id,review_ref\n2026-11-07,CS1@1,\n", "names no review"),
    ],
)
def test_a_malformed_review_file_is_an_error_never_a_lift(tmp_path, text, error):
    with pytest.raises(ReviewFileError, match=error):
        write(tmp_path / "r.csv", text).lifts("CS1@1", D[9])
