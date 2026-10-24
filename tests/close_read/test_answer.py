"""A4h criterion 1: the stamp decides. Only a list stamped today at or after 15:30 with every index counts."""

import pytest

from fno.close_read.answer import Refused, difference, read_answer
from tests.close_read.fakes import DAY, answer


@pytest.mark.parametrize("stamp", ["21-Oct-2026 15:30", "21-Oct-2026 15:31", "21-Oct-2026 19:55"])
def test_a_list_stamped_today_at_or_after_the_close_counts(stamp):
    got = read_answer(answer(stamp), DAY)
    assert got.stamp == stamp and got.values["NIFTY 50"] == {
        "last": 22811.35,
        "open": 23016.0,
        "high": 23120.9,
        "low": 22649.9,
        "previous_close": 22888.95,
    }
    assert set(got.values) == {"NIFTY 50", "NIFTY BANK", "INDIA VIX"}


@pytest.mark.parametrize(
    ("stamp", "why"),
    [
        ("21-Oct-2026 15:29", "NSE stamp 21-Oct-2026 15:29 is before 15:30"),  # today, before the close
        ("19-Oct-2026 15:30", "NSE stamp 19-Oct-2026 15:30 is not today's session"),  # the previous session
        ("", "NSE answer has no timestamp"),
        ("tomorrow", "NSE stamp 'tomorrow' is not readable"),
    ],
)
def test_any_other_stamp_is_refused_with_its_reason(stamp, why):
    with pytest.raises(Refused, match="^" + why.replace("(", r"\(").replace(")", r"\)") + "$"):
        read_answer(answer(stamp), DAY)


def test_a_missing_index_or_an_unreadable_value_is_refused():
    with pytest.raises(Refused, match="NIFTY BANK missing from the answer"):
        read_answer(answer(drop=("NIFTY BANK",)), DAY)
    with pytest.raises(Refused, match="INDIA VIX has no readable last$"):
        broken = answer()
        broken["data"][-1]["last"] = "-"
        read_answer(broken, DAY)
    with pytest.raises(Refused, match="NIFTY 50 missing"):
        read_answer({"timestamp": "21-Oct-2026 15:30", "error": "page"}, DAY)  # an error page with no rows


def test_a_difference_is_same_or_its_size_never_a_level():
    assert difference(22811.35, 22811.35) == "same" and difference(22811.35, 22811.40) == "differs by 0.05"
