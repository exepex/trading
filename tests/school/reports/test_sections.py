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
    assert "CS1@1 BANKNIFTY-M: net Rs +138 (profit_target)" in lines
    assert "CS1@1 BANKNIFTY-M: 3 / 2 / 1" in lines and "N0@1 BANKNIFTY-M: 3" not in lines
    total = "Fleet total, rule drivers only: Rs +138 (separate hypothetical accounts, not one budget)"
    assert total in lines, "the control's -50 and the ticket's 999 are not in it"
    assert "Control (not in the fleet total): N0@1 BANKNIFTY-M net Rs -50" in lines


def test_an_empty_day_says_none_and_is_red():
    text = evening()
    lines = "\n".join(text.lines)
    assert (
        text.banner is Banner.RED
        and "Trades closed: none" in lines
        and "Fleet total, rule drivers only: Rs +0" in lines
    )


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


def test_when_only_a_control_trades_the_evening_is_red_and_the_fleet_total_stays_zero():
    records = [f.trade_by("N0@1"), f.net_record("N0@1", 5000.0)]
    text = evening(records)
    lines = "\n".join(text.lines)
    assert text.banner is Banner.RED, "no rule driver is a candidate, as in the morning"
    assert "Trades closed: none" in lines and "Fleet total, rule drivers only: Rs +0" in lines
    assert "Control (not in the fleet total): N0@1 BANKNIFTY-M net Rs +5,000" in lines


def test_measurement_only_drivers_have_their_own_line_and_are_not_in_the_fleet_total():
    records = [trade_record(), f.net_record("CS1@1", 100.0), f.net_record("PS5@1", -400.0)]
    lines = "\n".join(evening(records).lines)
    assert "Measurement only (not in the fleet total): PS5@1 BANKNIFTY-M net Rs -400" in lines
    assert "Fleet total, rule drivers only: Rs +100" in lines


def test_a_rule_drivers_trade_keeps_the_evening_amber_whatever_the_controls_do():
    records = [trade_record(), f.trade_by("N0@1"), f.net_record("CS1@1", 100.0)]
    assert evening(records).banner is Banner.AMBER


WHY = "CS1@1 BANKNIFTY-M: net Rs -140; why: wrong direction (also: costs ate the edge); hard road"


def with_why(*causes, records=()):
    return HowDidTodayGoSection(f.Day(tuple(records), (), (), tuple(causes))).render(f.SESSION)


def test_the_instructors_lines_are_shown_verbatim_under_a_header_after_the_counts():
    lines = with_why(WHY, records=[trade_record(), f.net_record("CS1@1", -140.0)]).lines
    at = lines.index("Why (the instructor's words):")
    assert lines[at + 1] == WHY
    counts_at = lines.index("Counts (eligible / fillable / executed):")
    assert counts_at < at < next(i for i, line in enumerate(lines) if line.startswith("Fleet total")), (
        "after the counts, before the fleet total"
    )


def test_no_instructor_lines_means_no_header_and_no_change():
    assert "Why (the instructor's words):" not in "\n".join(with_why().lines)
    assert with_why().lines == evening().lines


def test_a_line_about_a_control_or_a_measurement_only_driver_is_left_out_of_the_why_lines():
    control = "N0@1 BANKNIFTY-M: net Rs +5000; why: lucky"
    measurement = "PS5@1 BANKNIFTY-M: net Rs -400; why: wrong direction"
    lines = with_why(control, WHY, measurement).lines
    assert WHY in lines and control not in lines and measurement not in lines


def test_only_controls_in_the_why_lines_leave_no_header():
    assert "Why (the instructor's words):" not in "\n".join(with_why("N0@1 BANKNIFTY-M: net Rs +5000; why: x").lines)


def test_a_tickets_line_is_not_shown_because_a_ticket_is_never_in_rupees():
    ticket = "CS1@1 BANKNIFTY-M ticket: net Rs -90; why: wrong direction"
    updated = "CS1@1 BANKNIFTY-M: net Rs -140; why: wrong direction (updated)"
    lines = with_why(ticket, updated).lines
    assert ticket not in lines and updated in lines


def test_the_pinned_format_is_what_the_instructors_why_line_writes():
    """MS-INS part e's `why_line` starts with the driver id, a space and the road (the MS-P1j builder's contract)."""
    outputs = pytest.importorskip(
        "fno.school.instructor.outputs.why_line", reason="MS-INS part e is not on this branch"
    )
    assert outputs.LINE.startswith("{driver} {road}{ticket}: net Rs ")
    assert WHY.startswith("CS1@1 BANKNIFTY-M: net Rs ") and "ticket" in outputs.LINE
