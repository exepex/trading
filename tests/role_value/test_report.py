"""Story F9a end to end on a temporary journal (criteria 3, 5, 6, 10): one scored pair on 2 Nov 2026, the real run
buys the call (Rs 1,460 net, `unit_fixture`) and the shadow does not trade; book 2's only usage is 30 minutes that day
and the plan Rs 3,000, so the day costs Rs 3,000 split over three units: macro's net value is 1,460 - 1,000 = Rs 460.
C4's log blocks one opportunity with two failed checks: 2 caught violations, 1 prevented action."""

from datetime import date

from fno.budget.allocation import allocate
from fno.constants import Decision
from fno.role_value.render import NO_ROWS, render
from fno.role_value.report import Period
from fno.role_value.wiring import role_value_report_from
from fno.scoreboard.ports import ProtocolStatus
from tests.role_value.builders import BOOK, row, usage, write_role_units, write_rows, write_shadow
from tests.role_value.unit_fixture import DAY, LOTS, QUOTES, setup
from tests.scoreboard.matched_builders import Calendar, Settlements, Snapshots, record, write_run

USAGE = [usage(DAY, "30.00")]
C4_LOG = ("day,book,opportunity_id,mode,check,reason,numbers\n"
          f"{DAY},{BOOK},o2,entry,max_loss,too big,{{}}\n{DAY},{BOOK},o2,entry,margin,short,{{}}\n")  # fmt: skip


def report(root, plan=3_000.0):
    return role_value_report_from(root, LOTS, Calendar().sessions, Snapshots(QUOTES), Settlements(),
                                  ProtocolStatus(None, False), lambda month: allocate(month, plan, USAGE),
                                  lambda month: USAGE)  # fmt: skip


def journal(root, rows):
    run_id = f"{DAY.isoformat()}-{BOOK}"
    pack = setup(root, real_run=run_id)
    write_run(root, BOOK, DAY, record("o1", pack=pack), pack=pack)
    write_shadow(root, DAY, record("o1", Decision.NO_TRADE, "no trade", legs=(), pack=pack))
    write_role_units(root)
    write_rows(root, rows)
    log = root / "journal" / BOOK / "validity_failures.csv"
    log.write_text(C4_LOG)


def period(review=False, start=date(2026, 11, 2)):
    return Period(BOOK, date(2026, 11, 1), date(2026, 11, 30), start, review)


def test_one_pair_reproduces_the_hand_computation(tmp_path):
    journal(tmp_path, [row(DAY, "macro")])
    result = report(tmp_path).build(period())
    macro = {s.unit: s for s in result.scores}["macro"]
    assert (macro.applicable, macro.changed, macro.mean_difference, macro.cost, macro.mean_net_value) == (
        1, 1, 1460.0, 1000.0, 460.0)  # fmt: skip
    assert macro.interval is None  # fewer than one block of 20: no bootstrap, so no verdict either
    assert (result.controls.caught_violations, result.controls.prevented_actions) == (2, 1)
    text = render(result)
    assert "| macro | 1 | 1 | 1,460.00 | 1,000.00 | 460.00 |" in text and "no profit figure" in text


def test_a_month_without_plan_cost_is_unknown_with_no_verdict(tmp_path):
    journal(tmp_path, [row(DAY, "macro")])
    result = report(tmp_path, plan=None).build(period(review=True))
    macro = {s.unit: s for s in result.scores}["macro"]
    assert macro.cost is None and macro.mean_net_value is None
    assert result.verdicts["macro"].startswith("no verdict")
    assert "unknown" in render(result)


def test_unavailable_shadows_and_unconsulted_cards_are_counted_apart(tmp_path):
    rows = [row(DAY, "macro", status="shadow_unavailable", pack="", snap="x")]
    journal(tmp_path, rows)
    result = report(tmp_path).build(period())
    assert result.excluded == {"shadow_unavailable": 1}
    assert {s.unit: s.applicable for s in result.scores}["macro"] == 0


def test_no_rows_says_so(tmp_path):
    journal(tmp_path, [])
    assert NO_ROWS in render(report(tmp_path).build(period()))


def test_a_day_the_ablated_unit_s_card_was_not_consulted_does_not_apply(tmp_path):
    journal(tmp_path, [row(DAY, "macro", consulted=("positioning", "vol"))])
    result = report(tmp_path).build(period())
    assert result.excluded == {"card not consulted (not applicable)": 1}
    assert {s.unit: s.cost for s in result.scores}["positioning"] == 1500.0  # Rs 3,000 over the two consulted


def test_rows_before_the_common_start_are_pilot_never_scored(tmp_path):
    journal(tmp_path, [row(DAY, "macro")])
    result = report(tmp_path).build(period(start=date(2026, 11, 3)))
    assert result.excluded == {"pilot, before the common start": 1}
    assert {s.unit: s.applicable for s in result.scores} == {}
