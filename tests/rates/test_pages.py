"""RBI's pages parsed (story A21, criteria 1-3): the 14 Oct 2026 release and the 16 Oct home page; a changed layout is
refused with the field named."""

import pytest

from fno.rates.pages import RatePageError, parse_current_rates, parse_tbill_release, tbill_release_ids

from .helpers import HOME, LIST, RELEASE


def text(data):
    return data.decode("utf-8", errors="replace")


def test_the_14_october_release():
    auction = parse_tbill_release(text(RELEASE), 63803)
    assert auction.auction_date.isoformat() == "2026-10-14" and auction.release_no == "2026-2027/1325"
    assert auction.yields_pct == (5.7281, 6.2896, 6.4891)


def test_the_home_page_box():
    rates = parse_current_rates(text(HOME))
    assert (rates.policy_repo_pct, rates.tbill_91_pct) == (5.50, 5.7281)


def test_the_list_keeps_only_the_exact_title():
    assert tbill_release_ids(text(LIST)) == [63803]
    near = text(LIST).replace("T-Bill Auction Result: Cut-off</a>", "T-Bill Auction Result: Cut-off (revised)</a>")
    assert tbill_release_ids(near) == []
    assert tbill_release_ids("") == []


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [("(YTM: 6.4891%)", "(Yield 6.4891%)", "'YTM' found 2 times"), ("Date : Oct 14, 2026", "On 14 Oct", "'date'"),
     ("Press Release: 2026-2027/1325", "Release 1325", "'release number'"),
     ("91-Day, 182-Day and 364-Day T-Bill Auction Result: Cut-off", "Auction Result", "'title'")],
)  # fmt: skip
def test_a_changed_release_layout_names_the_field(old, new, field):
    with pytest.raises(RatePageError, match=field):
        parse_tbill_release(text(RELEASE).replace(old, new), 63803)


@pytest.mark.parametrize(("old", "field"), [("Policy Repo Rate", "'Policy Repo Rate'"),
                                            ("91 day T-bills", "'91 day T-bills'")])  # fmt: skip
def test_a_changed_home_layout_names_the_field(old, field):
    with pytest.raises(RatePageError, match=field):
        parse_current_rates(text(HOME).replace(old, "Something else"))
