"""Criteria 2-6 (story MS-P1g): the sections say Paper, the banner is red or amber, a planted refusal shows, no
contract, strike or card internal appears, and both carry the NSE-terms and no-latency lines."""

import re

import pytest

from fno.school.constants import NO_LATENCY_LABEL, NSE_TERMS_LINE, PAPER_LABEL, ClosureReason, DriverRole
from fno.school.contracts.reports import Banner, ReportSection
from fno.school.reports.banner import AMBER_MEANING, RED_MEANING, banner_for
from fno.school.reports.evening import HowDidTodayGoSection
from fno.school.reports.today import TodaySection
from tests.school.contracts.test_records import closed_record, trade_record
from tests.school.reports import fakes as f


def today(**kw):
    return TodaySection(f.Today(**kw)).render(f.SESSION)


def evening(items=(), rows=()):
    return HowDidTodayGoSection(f.Day(tuple(items), tuple(rows))).render(f.SESSION)


def test_both_sections_are_report_sections_and_say_paper():
    for section in (TodaySection(f.Today()), HowDidTodayGoSection(f.Day())):
        assert isinstance(section, ReportSection)
        assert PAPER_LABEL in section.render(f.SESSION).title


def test_banner_has_no_green_and_every_input_maps_to_red_or_amber():
    assert {m.value for m in Banner} == {"red", "amber"}
    assert {banner_for(c, n) for c in (0, 1, 5) for n in (0, 1, 9)} <= set(Banner)
    assert banner_for(0, 1) is Banner.AMBER


@pytest.mark.parametrize("closed,candidates,expected", [(0, 1, Banner.AMBER), (1, 1, Banner.RED), (0, 0, Banner.RED)])
def test_the_banner_is_red_on_a_closed_road_or_no_candidate_else_amber(closed, candidates, expected):
    assert banner_for(closed, candidates) is expected


def test_today_lists_open_and_closed_roads_the_plan_with_worst_loss_and_the_amber_banner():
    text = today(days=f.roads_with_one_closed())
    lines = "\n".join(text.lines)
    assert text.banner is Banner.RED and "FINNIFTY-M closed (lot_mismatch)" in lines  # a closed road is red
    assert "CS1@1 BANKNIFTY-M: PCS, worst loss Rs 2,500" in lines and RED_MEANING in lines
    amber = today()
    assert amber.banner is Banner.AMBER and AMBER_MEANING in "\n".join(amber.lines)


def test_today_with_no_candidate_is_red_and_says_so():
    text = today(trades=())
    assert text.banner is Banner.RED and "No candidate today" in "\n".join(text.lines)


def test_controls_and_measurement_only_drivers_are_never_shown_as_candidates():
    trades = (f.plan("CS1@1"), f.plan("N0@1", DriverRole.CONTROL), f.plan("PS5@1", DriverRole.MEASUREMENT_ONLY))
    lines = "\n".join(today(trades=trades).lines)
    assert "CS1@1" in lines and "N0@1" not in lines and "PS5@1" not in lines


def test_a_refusal_planted_in_the_input_appears_in_the_evening_section():
    lines = "\n".join(evening([f.refused_record()]).lines)
    assert "refused: CS1@1 NIFTY-M, max_loss" in lines


def test_a_closed_road_in_the_evening_is_listed_and_makes_the_banner_red():
    text = evening([trade_record(), closed_record(ClosureReason.HASH_MISMATCH)])
    assert text.banner is Banner.RED and "road_closed: N0@1 BANKNIFTY-M, hash_mismatch" in "\n".join(text.lines)


def test_the_evening_shows_each_rule_trades_net_the_counts_and_the_labelled_fleet_total():
    records = [
        trade_record(),
        f.net_record("CS1@1", 137.7),
        f.net_record("N0@1", -50.0),
        f.net_record("CS1@1", 999.0, True),
    ]
    lines = "\n".join(evening(records, [f.counts(), f.counts("N0@1")]).lines)
    assert "CS1@1 BANKNIFTY-M: net Rs +138 (profit_target)" in lines and "N0@1 BANKNIFTY-M: net" not in lines
    assert "CS1@1 BANKNIFTY-M: 3 / 2 / 1" in lines and "N0@1 BANKNIFTY-M: 3" not in lines
    assert "Fleet total: Rs +88 (separate hypothetical accounts, not one budget)" in lines  # the ticket's 999 is out


def test_an_empty_day_says_none_and_is_red():
    text = evening()
    lines = "\n".join(text.lines)
    assert text.banner is Banner.RED and "Trades closed: none" in lines and "Fleet total: Rs +0" in lines


def test_both_sections_carry_the_nse_terms_line_and_the_no_latency_label():
    for text in (today(), evening([trade_record()])):
        assert NO_LATENCY_LABEL in text.lines and NSE_TERMS_LINE in text.lines
        assert "no latency [reasoning only]" in NO_LATENCY_LABEL


def test_no_contract_strike_price_or_card_internal_appears_in_either_section():
    record = trade_record()
    proposal = record.decision.proposal
    planted = {str(leg.key.strike) for leg in proposal.legs} | {leg.key.expiry.isoformat() for leg in proposal.legs}
    planted |= {str(q.quote.bid) for q in record.witnessed} | {str(proposal.net_premium), record.card_sha256}
    planted |= {record.snapshot_id, record.snapshot_sha256, "expected_move", "812.5"}
    for text in (today(), evening([record, f.refused_record(), f.net_record()], [f.counts()])):
        body = "\n".join((text.title, *text.lines))
        assert not [p for p in planted if p in body], f"leaked: {[p for p in planted if p in body]}"
        assert not re.search(r"\b\d{4,}(\.\d+)?\s?(CE|PE)\b", body)
