"""The checks and the as-of reader (story A21, criteria 4, 6 and 7), boundaries included."""

from datetime import date, datetime, timedelta

import pytest

from fno.models import IST
from fno.rates.as_of import RatesAsOf
from fno.rates.checks import disagreement, stale_auction, stale_home
from fno.rates.constants import POLICY_REPO, TBILL_91
from fno.rates.rows import RateRow

NOW = datetime(2026, 10, 22, 18, 40, tzinfo=IST)


def row(rate=TBILL_91, day="2026-10-14", value="5.7281", seen=NOW - timedelta(days=2), release="2026-2027/1325"):
    return RateRow(rate, day, value, release, "url", "sha", seen.isoformat(), "live", "prid=1")


@pytest.mark.parametrize(("today", "stale"), [(date(2026, 10, 22), False), (date(2026, 10, 23), True)])
def test_an_auction_8_days_old_is_clean_and_9_days_stale(today, stale):
    assert (stale_auction([row()], today) is not None) == stale
    assert stale_auction([], today) is None  # a first run has nothing to be stale against


@pytest.mark.parametrize(("age", "stale"), [(timedelta(hours=48), False), (timedelta(hours=48, seconds=1), True)])
def test_a_home_read_48_hours_old_is_clean_and_one_second_more_stale(age, stale):
    assert (stale_home(NOW - age, NOW) is not None) == stale
    assert stale_home(None, NOW) is None


def test_the_home_page_matching_the_newest_release_is_clean():
    assert disagreement([row()], 5.7281, NOW) is None
    assert disagreement([], 5.7281, NOW) is None


@pytest.mark.parametrize(("age", "flagged"), [(timedelta(hours=23, minutes=59), False), (timedelta(hours=24), True)])
def test_the_release_before_is_accepted_only_while_the_newest_is_under_24_hours_old(age, flagged):
    older = row(day="2026-10-14", value="5.7281", seen=NOW - timedelta(days=7))
    newest = row(day="2026-10-21", value="5.7100", seen=NOW - age, release="2026-2027/1400")
    assert (disagreement([older, newest], 5.7281, NOW) is not None) == flagged


def test_a_figure_matching_neither_release_is_a_disagreement():
    older = row(day="2026-10-14", seen=NOW - timedelta(days=7))
    newest = row(day="2026-10-21", value="5.7100", seen=NOW - timedelta(hours=1), release="2026-2027/1400")
    assert "disagreement: the home page shows 91-day 5.6000%" in disagreement([older, newest], 5.6, NOW)


def test_as_of_never_looks_ahead():
    cutoff = datetime(2026, 10, 16, 14, 30, tzinfo=IST)
    rows = [row(rate=POLICY_REPO, day="2026-10-16", value="5.50", seen=cutoff - timedelta(seconds=1)),
            row(rate=POLICY_REPO, day="2026-10-16", value="5.25", seen=cutoff + timedelta(seconds=1))]  # fmt: skip
    assert RatesAsOf(rows).value(POLICY_REPO, cutoff).value_pct == "5.50"
    exactly = [row(rate=POLICY_REPO, value="5.75", seen=cutoff)]
    assert RatesAsOf(exactly).value(POLICY_REPO, cutoff).value_pct == "5.75"  # at the cutoff: known
    assert RatesAsOf([]).value(POLICY_REPO, cutoff) is None
